def extract_reply(response):
    """
    Robust extraction for all Gemini model formats.
    Handles:
    - response.text
    - response.candidates[0].content
    - response.candidates[0].parts[x].text
    - response.output
    - message objects with role/model/parts
    """

    # 1. Direct text (old SDK)
    if hasattr(response, "text") and response.text:
        return response.text

    # 2. Candidates list
    if hasattr(response, "candidates") and response.candidates:
        c = response.candidates[0]

        # a) content attribute (common in Gemini 1.5)
        if hasattr(c, "content") and c.content:
            return c.content
        
        # b) parts list inside candidates
        if hasattr(c, "parts") and c.parts:
            part_texts = []
            for p in c.parts:
                if hasattr(p, "text") and p.text:
                    part_texts.append(p.text)
                elif isinstance(p, dict) and "text" in p:
                    part_texts.append(p["text"])
            if part_texts:
                return "\n".join(part_texts)

        # fallback
        return str(c)

    # 3. Output list (Gemini 3 format)
    if hasattr(response, "output") and response.output:
        part_texts = []
        for out in response.output:
            if hasattr(out, "content") and out.content:
                part_texts.append(out.content)
            if hasattr(out, "text") and out.text:
                part_texts.append(out.text)
        if part_texts:
            return "\n".join(part_texts)
    
    # 4. Message objects (parts=null)
    if hasattr(response, "parts") and response.parts:
        part_texts = []
        for p in response.parts:
            if hasattr(p, "text") and p.text:
                part_texts.append(p.text)
        if part_texts:
            return "\n".join(part_texts)

    # 5. LAST fallback: string representation
    return str(response)
