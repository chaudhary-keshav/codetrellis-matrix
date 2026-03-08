"""
LangChainExtractor - Extracts LangChain components from Python source code.

This extractor parses LangChain code and extracts:
- Chain definitions (LLMChain, SequentialChain, etc.)
- Agent configurations
- Tool definitions
- Prompt templates
- Memory configurations
- Retriever/RAG components
- Vector store integrations
- LLM/ChatModel configurations

Part of CodeTrellis v2.0 - Python AI/ML Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class ChainType(Enum):
    """Types of LangChain chains."""
    LLM_CHAIN = "LLMChain"
    SEQUENTIAL = "SequentialChain"
    ROUTER = "RouterChain"
    RETRIEVAL_QA = "RetrievalQA"
    CONVERSATIONAL = "ConversationalRetrievalChain"
    STUFF = "StuffDocumentsChain"
    MAP_REDUCE = "MapReduceDocumentsChain"
    REFINE = "RefineDocumentsChain"
    LCEL = "LCEL"  # LangChain Expression Language


@dataclass
class LLMInfo:
    """Information about an LLM configuration."""
    name: str
    provider: str  # openai, anthropic, huggingface, ollama, etc.
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    streaming: bool = False
    api_key_env: Optional[str] = None


@dataclass
class PromptTemplateInfo:
    """Information about a prompt template."""
    name: str
    template_type: str  # PromptTemplate, ChatPromptTemplate, FewShotPromptTemplate
    input_variables: List[str] = field(default_factory=list)
    template_preview: Optional[str] = None
    partial_variables: List[str] = field(default_factory=list)


@dataclass
class ChainInfo:
    """Information about a LangChain chain."""
    name: str
    chain_type: str
    llm: Optional[str] = None
    prompt: Optional[str] = None
    memory: Optional[str] = None
    retriever: Optional[str] = None
    tools: List[str] = field(default_factory=list)
    output_key: Optional[str] = None
    verbose: bool = False
    is_lcel: bool = False
    line_number: int = 0


@dataclass
class AgentInfo:
    """Information about a LangChain agent."""
    name: str
    agent_type: str  # zero-shot-react, openai-functions, etc.
    llm: Optional[str] = None
    tools: List[str] = field(default_factory=list)
    memory: Optional[str] = None
    max_iterations: Optional[int] = None
    verbose: bool = False


@dataclass
class ToolInfo:
    """Information about a LangChain tool."""
    name: str
    description: Optional[str] = None
    func: Optional[str] = None
    return_direct: bool = False
    is_builtin: bool = False
    args_schema: Optional[str] = None


@dataclass
class VectorStoreInfo:
    """Information about a vector store configuration."""
    name: str
    store_type: str  # FAISS, Pinecone, Chroma, Weaviate, etc.
    embedding_model: Optional[str] = None
    index_name: Optional[str] = None
    collection_name: Optional[str] = None
    persist_directory: Optional[str] = None


@dataclass
class RetrieverInfo:
    """Information about a retriever configuration."""
    name: str
    retriever_type: str
    vector_store: Optional[str] = None
    search_type: str = "similarity"
    k: int = 4
    score_threshold: Optional[float] = None


@dataclass
class MemoryInfo:
    """Information about memory configuration."""
    name: str
    memory_type: str  # ConversationBufferMemory, ConversationSummaryMemory, etc.
    memory_key: str = "history"
    return_messages: bool = False
    input_key: Optional[str] = None
    output_key: Optional[str] = None


class LangChainExtractor:
    """
    Extracts LangChain components from source code.

    Handles:
    - LLM and ChatModel configurations
    - Chain definitions (traditional and LCEL)
    - Agent configurations
    - Tool definitions
    - Prompt templates
    - Memory types
    - Vector stores and retrievers
    - RAG pipelines
    """

    # LLM patterns
    LLM_PATTERNS = {
        'ChatOpenAI': re.compile(r'(\w+)\s*=\s*ChatOpenAI\s*\(\s*([^)]*)\s*\)'),
        'OpenAI': re.compile(r'(\w+)\s*=\s*OpenAI\s*\(\s*([^)]*)\s*\)'),
        'Anthropic': re.compile(r'(\w+)\s*=\s*(?:Chat)?Anthropic\s*\(\s*([^)]*)\s*\)'),
        'HuggingFaceHub': re.compile(r'(\w+)\s*=\s*HuggingFaceHub\s*\(\s*([^)]*)\s*\)'),
        'Ollama': re.compile(r'(\w+)\s*=\s*(?:Chat)?Ollama\s*\(\s*([^)]*)\s*\)'),
        'AzureChatOpenAI': re.compile(r'(\w+)\s*=\s*AzureChatOpenAI\s*\(\s*([^)]*)\s*\)'),
    }

    # Prompt template patterns
    PROMPT_TEMPLATE_PATTERN = re.compile(
        r'(\w+)\s*=\s*(PromptTemplate|ChatPromptTemplate|FewShotPromptTemplate|SystemMessagePromptTemplate|HumanMessagePromptTemplate)(?:\.from_template)?\s*\(\s*([^)]*(?:\([^)]*\)[^)]*)*)\s*\)',
        re.MULTILINE | re.DOTALL
    )

    # Chain patterns
    CHAIN_PATTERN = re.compile(
        r'(\w+)\s*=\s*(LLMChain|SequentialChain|SimpleSequentialChain|ConversationalRetrievalChain|RetrievalQA|StuffDocumentsChain|MapReduceDocumentsChain)\s*\(\s*([^)]*(?:\([^)]*\)[^)]*)*)\s*\)',
        re.MULTILINE | re.DOTALL
    )

    # LCEL chain pattern (pipe operator)
    LCEL_PATTERN = re.compile(
        r'(\w+)\s*=\s*([^=]+(?:\|[^=|]+)+)',
        re.MULTILINE
    )

    # Agent patterns
    AGENT_PATTERN = re.compile(
        r'(\w+)\s*=\s*(?:initialize_agent|create_\w+_agent|AgentExecutor)\s*\(\s*([^)]*(?:\([^)]*\)[^)]*)*)\s*\)',
        re.MULTILINE | re.DOTALL
    )

    # Tool patterns
    TOOL_DECORATOR = re.compile(r'@tool(?:\([^)]*\))?\s*\n\s*def\s+(\w+)')
    TOOL_CLASS = re.compile(r'(\w+)\s*=\s*Tool\s*\(\s*([^)]*(?:\([^)]*\)[^)]*)*)\s*\)')
    STRUCTURED_TOOL = re.compile(r'(\w+)\s*=\s*StructuredTool\.from_function\s*\(\s*([^)]*)\s*\)')

    # Vector store patterns
    VECTOR_STORE_PATTERNS = {
        'FAISS': re.compile(r'(\w+)\s*=\s*FAISS\.(?:from_documents|from_texts|load_local)\s*\(\s*([^)]*)\s*\)'),
        'Chroma': re.compile(r'(\w+)\s*=\s*Chroma(?:\.from_documents|\.from_texts)?\s*\(\s*([^)]*)\s*\)'),
        'Pinecone': re.compile(r'(\w+)\s*=\s*Pinecone(?:\.from_documents|\.from_texts)?\s*\(\s*([^)]*)\s*\)'),
        'Weaviate': re.compile(r'(\w+)\s*=\s*Weaviate(?:\.from_documents|\.from_texts)?\s*\(\s*([^)]*)\s*\)'),
    }

    # Retriever pattern
    RETRIEVER_PATTERN = re.compile(
        r'(\w+)\s*=\s*(\w+)\.as_retriever\s*\(\s*([^)]*)\s*\)'
    )

    # Memory patterns
    MEMORY_PATTERN = re.compile(
        r'(\w+)\s*=\s*(ConversationBufferMemory|ConversationSummaryMemory|ConversationBufferWindowMemory|ConversationTokenBufferMemory|VectorStoreRetrieverMemory)\s*\(\s*([^)]*)\s*\)'
    )

    def __init__(self):
        """Initialize the LangChain extractor."""
        pass

    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract all LangChain components from Python content.

        Args:
            content: Python source code

        Returns:
            Dict with chains, agents, tools, etc.
        """
        llms = self._extract_llms(content)
        prompts = self._extract_prompts(content)
        chains = self._extract_chains(content)
        agents = self._extract_agents(content)
        tools = self._extract_tools(content)
        vector_stores = self._extract_vector_stores(content)
        retrievers = self._extract_retrievers(content)
        memories = self._extract_memories(content)

        return {
            'llms': llms,
            'prompts': prompts,
            'chains': chains,
            'agents': agents,
            'tools': tools,
            'vector_stores': vector_stores,
            'retrievers': retrievers,
            'memories': memories
        }

    def _extract_llms(self, content: str) -> List[LLMInfo]:
        """Extract LLM configurations."""
        llms = []

        for provider, pattern in self.LLM_PATTERNS.items():
            for match in pattern.finditer(content):
                var_name = match.group(1)
                args_str = match.group(2)

                model_name = self._extract_string_arg(args_str, 'model') or \
                            self._extract_string_arg(args_str, 'model_name')
                temperature = self._extract_float_arg(args_str, 'temperature')
                max_tokens = self._extract_int_arg(args_str, 'max_tokens')
                streaming = 'streaming=True' in args_str

                llms.append(LLMInfo(
                    name=var_name,
                    provider=provider,
                    model_name=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    streaming=streaming
                ))

        return llms

    def _extract_prompts(self, content: str) -> List[PromptTemplateInfo]:
        """Extract prompt templates."""
        prompts = []

        for match in self.PROMPT_TEMPLATE_PATTERN.finditer(content):
            var_name = match.group(1)
            template_type = match.group(2)
            args_str = match.group(3)

            # Extract input variables
            input_vars = self._extract_list_arg(args_str, 'input_variables')

            # Try to extract template preview
            template_preview = self._extract_string_arg(args_str, 'template')
            if template_preview and len(template_preview) > 100:
                template_preview = template_preview[:100] + "..."

            prompts.append(PromptTemplateInfo(
                name=var_name,
                template_type=template_type,
                input_variables=input_vars,
                template_preview=template_preview
            ))

        return prompts

    def _extract_chains(self, content: str) -> List[ChainInfo]:
        """Extract chain definitions."""
        chains = []

        # Traditional chains
        for match in self.CHAIN_PATTERN.finditer(content):
            var_name = match.group(1)
            chain_type = match.group(2)
            args_str = match.group(3)

            llm = self._extract_var_arg(args_str, 'llm')
            prompt = self._extract_var_arg(args_str, 'prompt')
            memory = self._extract_var_arg(args_str, 'memory')
            retriever = self._extract_var_arg(args_str, 'retriever')
            verbose = 'verbose=True' in args_str

            chains.append(ChainInfo(
                name=var_name,
                chain_type=chain_type,
                llm=llm,
                prompt=prompt,
                memory=memory,
                retriever=retriever,
                verbose=verbose,
                line_number=content[:match.start()].count('\n') + 1
            ))

        # LCEL chains (pipe operator)
        for match in self.LCEL_PATTERN.finditer(content):
            var_name = match.group(1)
            chain_expr = match.group(2)

            # Check if it looks like an LCEL chain
            if '|' in chain_expr and any(kw in chain_expr for kw in ['prompt', 'llm', 'parser', 'retriever']):
                # Extract components from pipe expression
                components = [c.strip() for c in chain_expr.split('|')]

                chains.append(ChainInfo(
                    name=var_name,
                    chain_type="LCEL",
                    is_lcel=True,
                    tools=components,  # Store components as "tools" for now
                    line_number=content[:match.start()].count('\n') + 1
                ))

        return chains

    def _extract_agents(self, content: str) -> List[AgentInfo]:
        """Extract agent configurations."""
        agents = []

        for match in self.AGENT_PATTERN.finditer(content):
            var_name = match.group(1)
            args_str = match.group(2)

            # Extract agent type
            agent_type = self._extract_string_arg(args_str, 'agent') or \
                        self._extract_var_arg(args_str, 'agent_type') or \
                        "custom"

            llm = self._extract_var_arg(args_str, 'llm')
            tools = self._extract_var_arg(args_str, 'tools')
            memory = self._extract_var_arg(args_str, 'memory')
            max_iterations = self._extract_int_arg(args_str, 'max_iterations')
            verbose = 'verbose=True' in args_str

            agents.append(AgentInfo(
                name=var_name,
                agent_type=agent_type,
                llm=llm,
                tools=[tools] if tools else [],
                memory=memory,
                max_iterations=max_iterations,
                verbose=verbose
            ))

        return agents

    def _extract_tools(self, content: str) -> List[ToolInfo]:
        """Extract tool definitions."""
        tools = []

        # @tool decorator
        for match in self.TOOL_DECORATOR.finditer(content):
            func_name = match.group(1)
            tools.append(ToolInfo(
                name=func_name,
                func=func_name
            ))

        # Tool() class
        for match in self.TOOL_CLASS.finditer(content):
            var_name = match.group(1)
            args_str = match.group(2)

            name = self._extract_string_arg(args_str, 'name') or var_name
            description = self._extract_string_arg(args_str, 'description')
            func = self._extract_var_arg(args_str, 'func')
            return_direct = 'return_direct=True' in args_str

            tools.append(ToolInfo(
                name=name,
                description=description,
                func=func,
                return_direct=return_direct
            ))

        # StructuredTool.from_function
        for match in self.STRUCTURED_TOOL.finditer(content):
            var_name = match.group(1)
            args_str = match.group(2)

            func = self._extract_var_arg(args_str, 'func')
            name = self._extract_string_arg(args_str, 'name') or var_name
            description = self._extract_string_arg(args_str, 'description')
            args_schema = self._extract_var_arg(args_str, 'args_schema')

            tools.append(ToolInfo(
                name=name,
                description=description,
                func=func,
                args_schema=args_schema
            ))

        return tools

    def _extract_vector_stores(self, content: str) -> List[VectorStoreInfo]:
        """Extract vector store configurations."""
        vector_stores = []

        for store_type, pattern in self.VECTOR_STORE_PATTERNS.items():
            for match in pattern.finditer(content):
                var_name = match.group(1)
                args_str = match.group(2)

                embedding = self._extract_var_arg(args_str, 'embedding') or \
                           self._extract_var_arg(args_str, 'embeddings')

                vector_stores.append(VectorStoreInfo(
                    name=var_name,
                    store_type=store_type,
                    embedding_model=embedding,
                    index_name=self._extract_string_arg(args_str, 'index_name'),
                    collection_name=self._extract_string_arg(args_str, 'collection_name'),
                    persist_directory=self._extract_string_arg(args_str, 'persist_directory')
                ))

        return vector_stores

    def _extract_retrievers(self, content: str) -> List[RetrieverInfo]:
        """Extract retriever configurations."""
        retrievers = []

        for match in self.RETRIEVER_PATTERN.finditer(content):
            var_name = match.group(1)
            vector_store = match.group(2)
            args_str = match.group(3)

            search_type = self._extract_string_arg(args_str, 'search_type') or 'similarity'
            k = self._extract_int_arg(args_str, 'k') or 4

            retrievers.append(RetrieverInfo(
                name=var_name,
                retriever_type="VectorStoreRetriever",
                vector_store=vector_store,
                search_type=search_type,
                k=k
            ))

        return retrievers

    def _extract_memories(self, content: str) -> List[MemoryInfo]:
        """Extract memory configurations."""
        memories = []

        for match in self.MEMORY_PATTERN.finditer(content):
            var_name = match.group(1)
            memory_type = match.group(2)
            args_str = match.group(3)

            memory_key = self._extract_string_arg(args_str, 'memory_key') or 'history'
            return_messages = 'return_messages=True' in args_str

            memories.append(MemoryInfo(
                name=var_name,
                memory_type=memory_type,
                memory_key=memory_key,
                return_messages=return_messages
            ))

        return memories

    # Helper methods
    def _extract_string_arg(self, args_str: str, key: str) -> Optional[str]:
        match = re.search(rf'{key}\s*=\s*[\'"]([^"\']*)[\'"]', args_str)
        return match.group(1) if match else None

    def _extract_int_arg(self, args_str: str, key: str) -> Optional[int]:
        match = re.search(rf'{key}\s*=\s*(\d+)', args_str)
        return int(match.group(1)) if match else None

    def _extract_float_arg(self, args_str: str, key: str) -> Optional[float]:
        match = re.search(rf'{key}\s*=\s*([\d.]+)', args_str)
        return float(match.group(1)) if match else None

    def _extract_var_arg(self, args_str: str, key: str) -> Optional[str]:
        match = re.search(rf'{key}\s*=\s*(\w+)', args_str)
        return match.group(1) if match else None

    def _extract_list_arg(self, args_str: str, key: str) -> List[str]:
        match = re.search(rf'{key}\s*=\s*\[([^\]]+)\]', args_str)
        if match:
            return re.findall(r'[\'"]([^"\']+)[\'"]', match.group(1))
        return []

    def to_codetrellis_format(self, result: Dict[str, Any]) -> str:
        """Convert extracted LangChain data to CodeTrellis format."""
        lines = []

        # LLMs
        llms = result.get('llms', [])
        if llms:
            lines.append("[LANGCHAIN_LLMS]")
            for llm in llms:
                parts = [llm.name, f"provider:{llm.provider}"]
                if llm.model_name:
                    parts.append(f"model:{llm.model_name}")
                if llm.temperature is not None:
                    parts.append(f"temp:{llm.temperature}")
                if llm.streaming:
                    parts.append("streaming")
                lines.append("|".join(parts))
            lines.append("")

        # Chains
        chains = result.get('chains', [])
        if chains:
            lines.append("[LANGCHAIN_CHAINS]")
            for chain in chains:
                parts = [chain.name, f"type:{chain.chain_type}"]
                if chain.llm:
                    parts.append(f"llm:{chain.llm}")
                if chain.retriever:
                    parts.append(f"retriever:{chain.retriever}")
                if chain.is_lcel:
                    parts.append(f"components:[{' | '.join(chain.tools[:3])}...]")
                lines.append("|".join(parts))
            lines.append("")

        # Agents
        agents = result.get('agents', [])
        if agents:
            lines.append("[LANGCHAIN_AGENTS]")
            for agent in agents:
                parts = [agent.name, f"type:{agent.agent_type}"]
                if agent.llm:
                    parts.append(f"llm:{agent.llm}")
                if agent.tools:
                    parts.append(f"tools:[{','.join(agent.tools)}]")
                lines.append("|".join(parts))
            lines.append("")

        # Tools
        tools = result.get('tools', [])
        if tools:
            lines.append("[LANGCHAIN_TOOLS]")
            for tool in tools:
                parts = [tool.name]
                if tool.description:
                    desc = tool.description[:50] + "..." if len(tool.description) > 50 else tool.description
                    parts.append(f"desc:{desc}")
                if tool.args_schema:
                    parts.append(f"schema:{tool.args_schema}")
                lines.append("|".join(parts))
            lines.append("")

        # Vector stores
        vector_stores = result.get('vector_stores', [])
        if vector_stores:
            lines.append("[VECTOR_STORES]")
            for vs in vector_stores:
                parts = [vs.name, f"type:{vs.store_type}"]
                if vs.embedding_model:
                    parts.append(f"embeddings:{vs.embedding_model}")
                if vs.collection_name:
                    parts.append(f"collection:{vs.collection_name}")
                lines.append("|".join(parts))
            lines.append("")

        # Memories
        memories = result.get('memories', [])
        if memories:
            lines.append("[LANGCHAIN_MEMORY]")
            for mem in memories:
                parts = [mem.name, f"type:{mem.memory_type}"]
                parts.append(f"key:{mem.memory_key}")
                if mem.return_messages:
                    parts.append("return_messages")
                lines.append("|".join(parts))

        return "\n".join(lines)


# Convenience function
def extract_langchain(content: str) -> Dict[str, Any]:
    """Extract LangChain components from Python content."""
    extractor = LangChainExtractor()
    return extractor.extract(content)
