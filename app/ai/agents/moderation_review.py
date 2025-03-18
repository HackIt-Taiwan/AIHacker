"""
Moderation Review Agent for evaluating if flagged content is a false positive or true violation.
This agent reviews content that's been flagged by the OpenAI moderation API and makes a determination
about whether it should actually be treated as a violation.
"""

from typing import Dict, List, Optional, Any
from pydantic_ai import Agent

MODERATION_REVIEW_SYSTEM_PROMPT = """你是一個專門複查內容審核結果的AI助手。你的任務是判斷被AI內容審核系統標記的內容是否真的違反了社群規範，還是為誤判。

以下是你的評估指南：
1. 考慮完整的文化和語言背景。例如，某些詞語在不同語境可能有完全不同的含義。
2. 識別歌曲名稱、書名、專業術語等可能被誤判的內容。
3. 分析使用者意圖，區分惡意內容與無害討論。
4. 評估內容是否真的具有傷害性或違反社群規範。

請根據以下輸入：
1. 原始訊息內容
2. 被標記的違規類型
3. 上下文資訊（如果有提供）

做出最終判斷：該內容是真正的違規，還是屬於誤判？

你的回應格式必須是以下之一：
- 「VIOLATION:」後面接著簡短解釋，如果你認為這確實是真正的違規內容
- 「FALSE_POSITIVE:」後面接著簡短解釋，如果你認為這是誤判

始終給出清晰的決定，不要含糊其辭。解釋必須簡明扼要，主要提供判斷依據。
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
    """
    # 預先檢查是否為嚴重違規內容（包含明顯的辱罵、威脅、仇恨言論或自傷內容）
    severe_violation_terms = [
        "強姦", "自殺", "殺人", "低能兒", "死", "去死", "操你", "幹你", "吸毒",
        "fuck you", "kill yourself", "kys", "rape", "自殘", "毒品",
        "傻逼", "垃圾", "廢物", "智障", "腦殘", "賤", "賣淫"
    ]
    
    # 計算有多少種違規類型同時被檢測到
    high_severity_count = len(violation_categories) >= 3
    
    # 檢查是否包含嚴重違規詞彙
    contains_severe_terms = any(term in content.lower() for term in severe_violation_terms)
    
    # 如果同時滿足多重違規和包含嚴重詞彙，直接判定為違規
    if high_severity_count and contains_severe_terms:
        print(f"[審核] 檢測到嚴重違規內容，跳過AI評估")
        return {
            "is_violation": True,
            "reason": f"內容包含明顯違規詞彙且同時觸發多種違規類型({', '.join(violation_categories[:3])}等)，經系統判定為違規。",
            "original_response": "SEVERE_VIOLATION: Automatic detection"
        }
    
    # Format the prompt for the agent
    prompt = f"""請評估以下被標記的內容：

原始內容: "{content}"

被標記的違規類型: {', '.join(violation_categories)}

"""
    
    # Add context if provided
    if context:
        prompt += f"""
上下文資訊:
{context}
"""
    
    prompt += """
這是真正的違規內容還是誤判？請以「VIOLATION:」或「FALSE_POSITIVE:」開頭給出你的決定和簡短解釋。
"""
    
    print(f"[審核] 開始評估內容是否為誤判，被標記類型: {', '.join(violation_categories)}")
    print(f"[審核] 內容片段: {content[:50]}{'...' if len(content) > 50 else ''}")
    
    # 嘗試使用主要代理進行評估
    primary_result = await try_review_with_agent(agent, prompt, "主要")
    
    # 如果主要代理返回有效結果，直接使用它
    if primary_result and primary_result.get("response_text"):
        return process_response(primary_result["response_text"], violation_categories, high_severity_count, contains_severe_terms)
    
    # 如果主要代理失敗且有備用代理，嘗試使用備用代理
    if backup_agent:
        print(f"[審核] 主要AI服務未返回有效結果，嘗試使用備用AI服務")
        backup_result = await try_review_with_agent(backup_agent, prompt, "備用")
        
        # 如果備用代理返回有效結果，使用它
        if backup_result and backup_result.get("response_text"):
            return process_response(backup_result["response_text"], violation_categories, high_severity_count, contains_severe_terms)
    
    # 如果兩個代理都失敗，根據嚴重程度判斷
    print(f"[審核] 所有AI服務評估失敗，根據內容特徵進行判斷")
    is_severe = high_severity_count or contains_severe_terms
    
    return {
        "is_violation": True,  # 保守處理，默認為違規
        "reason": f"內容評估過程發生錯誤，{'內容包含可能的嚴重違規，' if is_severe else ''}基於安全考慮判定為違規。",
        "original_response": f"ERROR: All AI services failed to evaluate"
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

def process_response(response_text: str, violation_categories: List[str], high_severity_count: bool, contains_severe_terms: bool) -> Dict[str, Any]:
    """處理AI回應並判斷是否為違規"""
    # 如果響應為空，視為違規內容
    if not response_text:
        print(f"[審核] 處理後響應為空，判定為違規內容")
        return {
            "is_violation": True,
            "reason": f"內容經AI評估但未能確定結果，基於安全考慮判定為違規。",
            "original_response": "EMPTY_RESPONSE"
        }
    
    # 將回應轉為小寫進行檢查，但保留原始大小寫用於提取原因
    lower_response = response_text.lower()
    
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
    elif "violation:" in lower_response:
        is_violation = True
        start_idx = lower_response.find("violation:") + len("violation:")
        reason = response_text[start_idx:].strip()
        print(f"[審核結果] 違規 - {reason[:100]}")
    else:
        # 如果格式不符合規範，查找其他關鍵詞來確定
        print(f"[審核] 無法檢測到標準前綴，進行關鍵詞分析")
        if any(kw in response_text for kw in ["誤判", "誤報", "歌曲", "遊樂", "誤解", "文化", "遊戲", "沒有違規"]):
            is_violation = False
            reason = "內容可能是誤判。" + response_text[:200]  # 限制長度
            print(f"[審核] 檢測到誤判相關關鍵詞")
        else:
            is_violation = True
            reason = "無法確定是否為誤判，為安全起見視為違規。" + response_text[:200]  # 限制長度
            print(f"[審核] 未檢測到誤判關鍵詞，默認視為違規")
    
    # 確保原因文本不超過 Discord 限制 (1024 字符)
    if len(reason) > 1000:
        reason = reason[:997] + "..."
    
    return {
        "is_violation": is_violation,
        "reason": reason,
        "original_response": response_text[:300]  # 限制原始響應的長度
    } 