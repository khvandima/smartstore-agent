def make_agent_node(client):
    async def agent_node(state: AgentState) -> dict:
        tools = await client.get_tools()
        llm_with_tools = llm.bind_tools(tools)

        last_error = None
        for attempt in range(3):
            try:
                system = SystemMessage(content=f"""Ты Research & Analysis Agent — экспертный исследовательский ассистент.
                ## Стратегия поиска
                - Если вопрос про загруженные документы → используй search_documents
                - Если вопрос про текущие события или новости → используй web_search  
                - Если пользователь даёт ссылку на Google Doc → используй read_google_doc для чтения или ingest_google_docs для добавления в базу знаний
                - Если пользователь просит добавить документ (PDF или Markdown) → используй ingest_file с путём к файлу
                - Если вопрос требует сравнения или глубокого анализа → используй оба инструмента search_documents и web_search
                - Если не нашёл релевантной информации → честно скажи об этом, не придумывай
                ## Формат ответа
                - Отвечай структурированно: сначала прямой ответ, потом детали
                - Всегда указывай источник: "По данным документов..." или "По данным из интернета..."
                - Если информация из нескольких источников — сравни и синтезируй
                - Отвечай на том же языке что и вопрос пользователя
                ## Ограничения
                - Никогда не придумывай факты которых нет в источниках
                - Если информации недостаточно — предложи уточнить вопрос
                - Не повторяй вопрос пользователя в ответе
                Текущее время: {datetime.now().isoformat()}""")

                messages = [system] + state['messages']
                response = await llm_with_tools.ainvoke(messages)
                return {'messages': [response]}
            except Exception as e:
                last_error = e
                continue

        raise last_error

    return agent_node




async def make_tool_node(client):
    tools = await client.get_tools()
    return ToolNode(tools=tools)