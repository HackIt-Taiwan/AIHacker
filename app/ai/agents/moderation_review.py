"""
Moderation Review Agent for evaluating if flagged content is a false positive or true violation.
This agent reviews content that's been flagged by the OpenAI moderation API and makes a determination
about whether it should actually be treated as a violation.
"""

from typing import Dict, List, Optional, Any
from pydantic_ai import Agent

MODERATION_REVIEW_SYSTEM_PROMPT = """你是一個專門複查內容審核結果的AI助手。你的任務是判斷被AI內容審核系統標記的內容是否真的違反了社群規範，還是為誤判。你應該盡可能寬鬆地解釋內容，將更多案例判定為誤判而非違規。

以下是我們社群規範的精簡版本，請在做判斷時參考：

# HackIt 社群規範精簡版

## 1. 基本原則
- 1.1 尊重與包容：尊重所有社群成員，不論其背景、經驗水平或觀點。
- 1.2 建設性溝通：提供建設性的反饋，避免無意義的批評。
- 1.3 真誠互助：鼓勵互相幫助和知識分享。
- 1.4 共同責任：共同維護社群秩序。

## 2. 禁止行為
- 2.1 騷擾與霸凌：禁止任何形式的騷擾、霸凌或威脅行為。
- 2.2 仇恨言論：禁止基於個人特徵的仇恨或歧視言論。
- 2.3 不當內容：禁止分享色情、暴力或血腥內容。
- 2.4 個人隱私：禁止未經許可分享他人個人信息。
- 2.5 垃圾訊息：禁止發送垃圾訊息或過度標記他人。
- 2.6 損害性行為：禁止分享可能造成傷害的內容。
- 2.7 非法活動：禁止討論或促進非法活動。
- 2.8 惡意軟體：禁止分享惡意軟體或釣魚網站。

## 3. 內容指南
- 3.1 適當討論主題：確保討論主題與頻道相關。
- 3.2 敏感話題處理：保持客觀、尊重的態度。
- 3.3 知識產權尊重：分享內容時尊重知識產權。
- 3.4 語言使用：避免過度使用冒犯性語言，但理解台灣文化中的誇張表達（如「想死」、「笑死」等）通常是無害的。
- 3.5 圖片與媒體：避免分享不當圖片或媒體。
- 3.6 連結分享：確保分享的連結安全且適當。

## 4. 違規處理與文化理解
- 4.1 違規等級：五級處罰機制（5分鐘→12小時→7天→7天→28天）
- 4.2 申訴與文化理解：考慮台灣/華語文化背景的口語表達和語境。

你的評估指南：
1. 考慮完整的文化和語言背景。某些詞語在不同語境可能有不同的含義（參考規則 3.4 和 4.2）。
2. 識別歌曲名稱、書名、專業術語等可能被誤判的內容（參考規則 3.2 和 4.2）。
3. 分析使用者意圖，區分惡意內容與無害討論（參考規則 3.2）。
4. 評估內容是否真的具有傷害性或違反社群規範。
5. 特別注意台灣口語表達方式，許多包含「死」、「想死」、「快死了」、「去死」、「殺了你」等的表達只是誇張的口語表達方式，而非真正的自我傷害或暴力內容（參考規則 3.4 和 4.2）。
6. 對於部分粗俗語言、輕微髒話或開玩笑的表達，應傾向於判定為誤判，除非太過嚴重（參考規則 3.4）。

請根據以下輸入：
1. 原始訊息內容
2. 被標記的違規類型
3. 上下文資訊（如果有提供）

做出最終判斷：該內容是真正的違規，還是屬於誤判？

你的回應格式必須是以下之一，務必保持極度簡短（10-15字以內）：
- 「VIOLATION:」後面接著極簡短的違規原因，如果你認為這確實是真正的嚴重違規內容，並僅引用規則編號（例如「違反社群規章2.1：騷擾行為」）
- 「FALSE_POSITIVE:」後面接著極簡短的誤判原因，如果你認為這是誤判或只是輕微違規，並僅引用規則編號（例如「根據社群規章3.4：台灣口語」）

你的解釋必須極度簡短，不超過15個字，並只提供核心判斷依據。禁止使用長篇解釋。
"""

async def agent_moderation_review(model: Agent) -> Agent:
    """
    Create a moderation review agent for evaluating flagged content.
    
    Args:
        model: The AI model to use for the agent
        
    Returns:
        An agent configured for moderation review
    """
    agent = Agent(
        model,
        system_prompt=MODERATION_REVIEW_SYSTEM_PROMPT,
        name="moderation_review"
    )
    
    return agent

async def review_flagged_content(
    agent: Agent,
    content: str,
    violation_categories: List[str],
    context: Optional[str] = None,
    backup_agent: Optional[Agent] = None
) -> Dict[str, Any]:
    """
    Review content that has been flagged by the moderation system.
    
    Args:
        agent: The moderation review agent
        content: The flagged message content
        violation_categories: List of violation categories detected
        context: Optional context about the content (e.g., preceding messages)
        backup_agent: Optional backup agent to use if primary agent fails
        
    Returns:
        Dictionary with review results including:
        - is_violation: Boolean indicating if it's a true violation
        - reason: Explanation for the decision
        - rules_referenced: List of rule numbers referenced in the decision
    """
    # 檢查違規類型數量
    high_severity_count = len(violation_categories) >= 4
    
    # Format the prompt for the agent - 更強調文化語境和寬鬆判定
    prompt = f"""請評估以下被標記的內容：

原始內容: "{content}"

被標記的違規類型: {', '.join(violation_categories)}

評估指南：
1. 考慮台灣/華語文化背景，許多看似粗俗的表達只是日常用語（參考規則 3.4 和 4.2）
2. 在台灣的口語表達中，「想死」、「死了」、「去死」、「累死了」、「笑死」等包含「死」字的表達通常只是誇張的口語用法（參考規則 3.4）
3. 「幹」、「靠北」、「靠」等詞在台灣常被用作語氣詞或表達情緒，而非真正的侮辱（參考規則 3.4）
4. 只有確實的嚴重暴力、性相關或仇恨內容才應判定為違規（對照規則 2.1-2.8）
5. 請考慮訊息的完整語境和使用者意圖，而非單一字詞（參考規則 4.2）
6. 評估內容時，考慮是否符合特定的討論主題和適當的討論方式（參考規則 3.1 和 3.2）
"""
    
    # Add context if provided
    if context:
        prompt += f"""
上下文資訊:
{context}
"""
    
    prompt += """
這是真正的違規內容還是誤判？請以「VIOLATION:」或「FALSE_POSITIVE:」開頭給出你的決定和極度簡短的解釋（10-15字以內）。
記住：如有疑問，請傾向於判定為誤判。請確保在你的解釋中只簡單引用相關的規則編號，不要詳細解釋。
例如：「VIOLATION: 違反2.1：騷擾他人」或「FALSE_POSITIVE: 符合3.4：台灣口語」
"""
    
    print(f"[審核] 開始評估內容是否為誤判，被標記類型: {', '.join(violation_categories)}")
    print(f"[審核] 內容片段: {content[:50]}{'...' if len(content) > 50 else ''}")
    
    # 嘗試使用主要代理進行評估
    primary_result = await try_review_with_agent(agent, prompt, "主要")
    
    # 如果主要代理返回有效結果，直接使用它
    if primary_result and primary_result.get("response_text"):
        return process_response(primary_result["response_text"], violation_categories, high_severity_count)
    
    # 如果主要代理失敗且有備用代理，嘗試使用備用代理
    if backup_agent:
        print(f"[審核] 主要AI服務未返回有效結果，嘗試使用備用AI服務")
        backup_result = await try_review_with_agent(backup_agent, prompt, "備用")
        
        # 如果備用代理返回有效結果，使用它
        if backup_result and backup_result.get("response_text"):
            return process_response(backup_result["response_text"], violation_categories, high_severity_count)
    
    # 如果兩個代理都失敗，根據嚴重程度判斷
    print(f"[審核] 所有AI服務評估失敗，根據內容特徵進行判斷")
    is_severe = high_severity_count
    
    return {
        "is_violation": True,  # 保守處理，默認為違規
        "reason": f"內容可能違反規則2.1-2.8",
        "original_response": f"ERROR: All AI services failed to evaluate",
        "rules_referenced": ["2.1-2.8"]  # 默認引用所有禁止行為規則
    }

async def try_review_with_agent(agent: Agent, prompt: str, agent_type: str = "主要") -> Optional[Dict[str, Any]]:
    """嘗試使用特定代理進行評估"""
    try:
        print(f"[審核] 使用{agent_type}AI服務評估內容")
        run_result = await agent.run(prompt)
        
        # 處理響應
        response_text = ""
        
        # 首先嘗試訪問 data 屬性，這是 pydantic_ai 返回結果的常見屬性
        if hasattr(run_result, 'data'):
            response_text = run_result.data
            print(f"[審核] {agent_type}AI服務：使用 data 屬性獲取响應")
        # 備用選項
        elif hasattr(run_result, 'response'):
            response_text = run_result.response
            print(f"[審核] {agent_type}AI服務：使用 response 屬性獲取响應")
        elif hasattr(run_result, 'content'):
            response_text = run_result.content
            print(f"[審核] {agent_type}AI服務：使用 content 屬性獲取响應")
        elif hasattr(run_result, 'text'):
            response_text = run_result.text
            print(f"[審核] {agent_type}AI服務：使用 text 屬性獲取响應")
        elif hasattr(run_result, 'message'):
            response_text = run_result.message
            print(f"[審核] {agent_type}AI服務：使用 message 屬性獲取响應")
        elif isinstance(run_result, str):
            response_text = run_result
            print(f"[審核] {agent_type}AI服務：响應是直接的字符串")
        else:
            # 最後嘗試將結果轉換為字符串
            response_text = str(run_result)
            print(f"[審核] {agent_type}AI服務：无法直接獲取响應，已轉換為字符串")
        
        # 對響應文本進行處理
        if isinstance(response_text, str):
            original_text = response_text
            response_text = response_text.strip()
            
            # 移除可能包裹的引號
            if response_text.startswith('"') and response_text.endswith('"'):
                response_text = response_text[1:-1]
                print(f"[審核] {agent_type}AI服務：移除了雙引號")
            if response_text.startswith("'") and response_text.endswith("'"):
                response_text = response_text[1:-1]
                print(f"[審核] {agent_type}AI服務：移除了單引號")
            if response_text.startswith("「") and response_text.endswith("」"):
                response_text = response_text[1:-1]
                print(f"[審核] {agent_type}AI服務：移除了全形引號")
            
            # 檢查是否為空響應
            if not response_text or response_text.strip() == "":
                print(f"[審核] {agent_type}AI服務：收到空響應")
                return {"response_text": ""}
                
            print(f"[審核] {agent_type}AI服務：响應文本: {response_text[:100]}")
            return {"response_text": response_text}
        else:
            print(f"[審核] {agent_type}AI服務：响應不是字符串類型: {type(response_text)}")
            return {"response_text": ""}
            
    except Exception as e:
        print(f"[審核] {agent_type}AI服務評估失敗: {e}")
        return None

def process_response(response_text: str, violation_categories: List[str], high_severity_count: bool) -> Dict[str, Any]:
    """處理AI回應並判斷是否為違規"""
    # 如果響應為空，視為違規內容
    if not response_text:
        print(f"[審核] 處理後響應為空，判定為違規內容")
        return {
            "is_violation": True,
            "reason": f"內容經AI評估但未能確定結果，基於安全考慮判定為違規。",
            "original_response": "EMPTY_RESPONSE",
            "rules_referenced": ["2.1-2.8"]  # 默認引用所有禁止行為規則
        }
    
    # 將回應轉為小寫進行檢查，但保留原始大小寫用於提取原因
    lower_response = response_text.lower()
    
    # 提取引用的規則
    rule_pattern = r'規則\s*(\d+\.\d+(-\d+\.\d+)?)'
    import re
    rules_referenced = re.findall(rule_pattern, response_text)
    # 提取規則編號部分
    rules_referenced = [r[0] for r in rules_referenced] if rules_referenced else []
    
    if "false_positive" in lower_response:
        is_violation = False
        # 找到完整的解釋
        if "false_positive:" in lower_response:
            start_idx = lower_response.find("false_positive:") + len("false_positive:")
            reason = response_text[start_idx:].strip()
            print(f"[審核] 檢測到 false_positive: 前綴")
        else:
            reason = "這是一個誤判。" + response_text
            print(f"[審核] 檢測到 false_positive 關鍵詞但無前綴")
        print(f"[審核結果] 誤判 - {reason[:100]}")
        
        # 如果沒有引用規則，添加預設規則
        if not rules_referenced:
            rules_referenced = ["3.4", "4.2"]
    elif "violation:" in lower_response:
        is_violation = True
        start_idx = lower_response.find("violation:") + len("violation:")
        reason = response_text[start_idx:].strip()
        print(f"[審核結果] 違規 - {reason[:100]}")
        
        # 如果沒有引用規則，添加預設規則
        if not rules_referenced:
            rules_referenced = ["2.1-2.8"]
    else:
        # 如果格式不符合規範，查找其他關鍵詞來確定
        print(f"[審核] 無法檢測到標準前綴，進行關鍵詞分析")
        if any(kw in response_text for kw in ["誤判", "誤報", "歌曲", "遊樂", "誤解", "文化", "遊戲", "沒有違規"]):
            is_violation = False
            reason = "內容可能是誤判。" + response_text[:200]  # 限制長度
            print(f"[審核] 檢測到誤判相關關鍵詞")
            # 如果沒有引用規則，添加預設規則
            if not rules_referenced:
                rules_referenced = ["3.4", "4.2"]
        else:
            is_violation = True
            reason = "無法確定是否為誤判，為安全起見視為違規。" + response_text[:200]  # 限制長度
            print(f"[審核] 未檢測到誤判關鍵詞，默認視為違規")
            # 如果沒有引用規則，添加預設規則
            if not rules_referenced:
                rules_referenced = ["2.1-2.8"]
    
    # 確保原因文本不超過 Discord 限制 (1024 字符)
    if len(reason) > 1000:
        reason = reason[:997] + "..."
    
    return {
        "is_violation": is_violation,
        "reason": reason,
        "original_response": response_text[:300],  # 限制原始響應的長度
        "rules_referenced": rules_referenced
    } 