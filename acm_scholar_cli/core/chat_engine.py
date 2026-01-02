"""AI 对话引擎 - 处理论文相关的对话功能。"""

from typing import Optional, List
from acm_scholar_cli.config_manager import Config
from acm_scholar_cli.data.storage import DataStorage


class ChatEngine:
    """AI 对话引擎。"""

    def __init__(self, config: Config) -> None:
        """
        初始化对话引擎。

        Args:
            config: 配置对象
        """
        self.config = config
        self.current_paper_id: Optional[str] = None
        self.mode: str = "paper"  # 'paper' or 'global'
        self.last_sources: list = []
        self.gemini_client = None
        
        # 数据壁垒：初始化数据存储
        self.data_storage = DataStorage()
        self.current_session_id: Optional[str] = None
        
        self._setup_llm()

    def _setup_llm(self) -> None:
        """
        设置 LLM 提供商。
        """
        provider = self.config.llm.provider
        model = self.config.llm.model

        if provider == "gemini":
            self._setup_gemini(model)
        elif provider == "openai":
            self._setup_openai(model)
        elif provider == "deepseek":
            self._setup_deepseek(model)
        elif provider == "ollama":
            self._setup_ollama(model)
        else:
            # 默认使用 Gemini
            self._setup_gemini(model)

    def _setup_gemini(self, model: str) -> None:
        """
        设置 Gemini LLM。

        Args:
            model: 模型名称
        """
        try:
            from acm_scholar_cli.gemini import GeminiClient

            self.gemini_client = GeminiClient(
                api_key=self.config.llm.api_key,
                model=model or "gemini-1.5-pro",
            )
            self.llm = None  # Gemini uses its own client
        except ImportError:
            raise ImportError("请安装 google-generativeai: pip install google-generativeai")

    def _setup_openai(self, model: str) -> None:
        """
        设置 OpenAI LLM。

        Args:
            model: 模型名称
        """
        try:
            from langchain_openai import ChatOpenAI

            self.llm = ChatOpenAI(
                model=model or "gpt-4",
                api_key=self.config.llm.api_key,
                streaming=True,
            )
        except ImportError:
            raise ImportError("请安装 langchain-openai: pip install langchain-openai")

    def _setup_deepseek(self, model: str) -> None:
        """
        设置 DeepSeek LLM。

        Args:
            model: 模型名称
        """
        try:
            from langchain_openai import ChatOpenAI

            # DeepSeek 兼容 OpenAI API
            self.llm = ChatOpenAI(
                model=model or "deepseek-chat",
                api_key=self.config.llm.api_key,
                base_url="https://api.deepseek.com",
                streaming=True,
            )
        except ImportError:
            raise ImportError("请安装 langchain-openai: pip install langchain-openai")

    def _setup_ollama(self, model: str) -> None:
        """
        设置 Ollama 本地 LLM。

        Args:
            model: 模型名称
        """
        try:
            from langchain_community.llms import Ollama

            self.llm = Ollama(
                model=model or "llama2",
            )
        except ImportError:
            raise ImportError("请安装 langchain-community: pip install langchain-community")

    def set_mode(self, mode: str) -> None:
        """
        设置对话模式。

        Args:
            mode: 'paper' 或 'global'
        """
        self.mode = mode

    def set_model(self, model: str) -> None:
        """
        设置使用的模型。

        Args:
            model: 模型名称
        """
        self._setup_llm_with_model(model)

    def _setup_llm_with_model(self, model: str) -> None:
        """
        使用指定模型重新设置 LLM。

        Args:
            model: 模型名称
        """
        self._setup_llm()

    def load_paper(self, paper_id: str) -> bool:
        """
        加载论文到对话上下文。

        Args:
            paper_id: OpenAlex 论文 ID

        Returns:
            是否成功加载
        """
        self.current_paper_id = paper_id
        
        # 数据壁垒：开始新的阅读会话
        self.current_session_id = self.data_storage.start_reading_session(paper_id)
        
        # 如果使用 Gemini，初始化对话
        if self.gemini_client:
            system_instruction = f"""你是一个学术论文助手，正在帮助用户理解论文 {paper_id}。
请基于论文内容回答用户的问题，如果不确定，请明确说明。
回答应该专业、准确、有帮助。"""
            self.gemini_client.start_chat(system_instruction=system_instruction)
        
        return True

    def chat(self, question: str) -> str:
        """
        发送问题并获取回答。

        Args:
            question: 用户问题

        Returns:
            AI 回答
        """
        if self.mode == "global":
            return self._global_chat(question)
        else:
            return self._paper_chat(question)

    def _paper_chat(self, question: str) -> str:
        """
        与当前加载的论文对话。

        Args:
            question: 用户问题

        Returns:
            AI 回答
        """
        if not self.current_paper_id:
            return "请先加载论文，使用 /paper <paper_id> 命令"

        # 数据壁垒：记录问题到阅读会话
        if self.current_session_id:
            self.data_storage.add_question_to_session(self.current_session_id, question)

        # 构建提示
        prompt = f"""Based on the content of the paper, please answer the following question:

Question: {question}

Please provide a detailed answer based on the paper's content. If the answer cannot be found in the paper, please say so."""

        # 调用 LLM
        try:
            if self.gemini_client:
                response = self.gemini_client.chat(question)
            else:
                response = self.llm.invoke(prompt)
                response = response.content
            
            # 数据壁垒：保存 QA 对
            model_name = self.config.llm.model or self.config.llm.get_default_model()
            self.data_storage.save_qa_pair(
                paper_id=self.current_paper_id,
                question=question,
                answer=response,
                model=model_name,
            )
            
            return response
        except Exception as e:
            raise Exception(f"LLM 调用失败: {e}")

    def _global_chat(self, question: str) -> str:
        """
        在整个文库中搜索并回答。

        Args:
            question: 用户问题

        Returns:
            AI 回答
        """
        # 这里应该执行向量搜索
        prompt = f"""Based on the documents in the library, please answer the following question:

Question: {question}

Please search through all available documents and provide a comprehensive answer. Cite the sources you used."""

        try:
            if self.gemini_client:
                response = self.gemini_client.generate(prompt)
            else:
                response = self.llm.invoke(prompt)
                response = response.content
            
            # 数据壁垒：保存 QA 对 (全局模式)
            model_name = self.config.llm.model or self.config.llm.get_default_model()
            self.data_storage.save_qa_pair(
                paper_id="global",
                question=question,
                answer=response,
                model=model_name,
            )
            
            return response
        except Exception as e:
            raise Exception(f"LLM 调用失败: {e}")

    def summarize(self, length: str = "medium") -> str:
        """
        总结当前加载的论文。

        Args:
            length: 总结长度 ('short', 'medium', 'long')

        Returns:
            论文总结
        """
        if not self.current_paper_id:
            return "请先加载论文"

        length_instructions = {
            "short": "请用 1-2 段话简洁总结论文的主要贡献。",
            "medium": "请用 3-5 段话总结论文的主要观点、方法论和贡献。",
            "long": "请详细总结论文的每个部分，包括背景、方法、实验和结论。",
        }

        prompt = f"""请总结这篇论文的内容。

{length_instructions.get(length, length_instructions['medium'])}

请确保总结客观、准确，包含论文的核心信息。"""

        try:
            if self.gemini_client:
                response = self.gemini_client.generate(prompt)
            else:
                response = self.llm.invoke(prompt)
                response = response.content
            return response
        except Exception as e:
            raise Exception(f"LLM 调用失败: {e}")

    def get_last_sources(self) -> list:
        """
        获取上次回答的引用来源。

        Returns:
            来源列表
        """
        return self.last_sources

    def extract_concepts(self, question: str) -> list:
        """
        从问题中提取关键概念。

        Args:
            question: 用户问题

        Returns:
            概念列表
        """
        # 简单的关键词提取
        words = question.lower().split()
        # 移除常见停用词
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "do", "does", "did",
                     "what", "how", "why", "when", "where", "who", "which", "can", "could"}
        concepts = [w for w in words if w not in stopwords and len(w) > 2]
        return concepts

    def clear_context(self) -> None:
        """
        清空对话上下文。
        """
        # 数据壁垒：结束当前阅读会话
        if self.current_session_id:
            self.data_storage.end_reading_session(self.current_session_id)
            self.current_session_id = None
        
        self.current_paper_id = None
        self.last_sources = []

    def get_data_stats(self) -> dict:
        """
        获取数据积累统计。
        
        Returns:
            数据统计字典
        """
        return self.data_storage.get_all_stats()
