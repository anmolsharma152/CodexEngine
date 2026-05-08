from litellm import completion
import os

def rewrite_query_with_context(api_key, provider, model_name, chat_history, current_query):
    """
    Rewrites the user's query to be fully self-contained based on the chat history.
    """
    # If there is no history, just return the current query
    if not chat_history:
        return current_query

    # Format the recent history for the LLM (last 4 messages is usually enough)
    recent_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history[-4:]])
    
    prompt = f"""
    Given the following conversation history, rewrite the user's 'Follow-up Question' to be a fully standalone question. 
    It must contain all necessary context (like specific features, names, or concepts) mentioned previously.
    Do NOT answer the question, just rewrite it. If it is already standalone, return it exactly as is.

    Conversation History:
    {recent_history}

    Follow-up Question: {current_query}
    
    Standalone Question:
    """

    try:
        # We use a fast, cheap model for this if possible, but we'll stick to the user's chosen model for simplicity
        response = completion(
            model=f"{provider}/{model_name}",
            api_key=api_key,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0 # Strict and deterministic
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error rewriting query: {e}")
        return current_query # Fallback to original query if it fails

def generate_answer(api_key, provider, model_name, documents, metadatas, chat_history, current_query):
    try:
        os.environ[f"{provider.upper()}_API_KEY"] = api_key
        
        # UPGRADE: Format context to include visible metadata tags for the LLM
        context_blocks = []
        for doc, meta in zip(documents, metadatas):
            source_tag = f"[Source: {meta['source']} | Page: {meta['page']}]"
            context_blocks.append(f"{source_tag}\n{doc}\n")
            
        context_text = "\n---\n".join(context_blocks)
        
        # UPGRADE: Strict Citation Prompt Engineering
        system_prompt = f"""You are a highly capable, professional AI assistant. 
        Use the following retrieved context from the user's documents to answer their question. 
        
        CRITICAL INSTRUCTION: You MUST cite your sources. After every factual sentence you write, you must append the citation using the exact Source and Page provided in the context blocks.
        Example format: "The application requires a restart to apply the theme [Source: manual.pdf | Page: 12]."
        
        If the answer is not in the context, clearly state that you do not know based on the provided documents.
        
        Context:
        {context_text}
        """

        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in chat_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        messages.append({"role": "user", "content": current_query})

        response = completion(
            model=f"{provider.lower()}/{model_name}",
            messages=messages
        )
        
        return response.choices[0].message.content

    except Exception as e:
        return f"Error connecting to {provider.capitalize()}: {str(e)}"