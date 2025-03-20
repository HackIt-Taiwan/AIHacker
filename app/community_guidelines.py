"""
Community guidelines in Traditional Chinese based on OpenAI's content policy categories.
"""

from typing import Dict, List, Tuple

# Mapping of violation categories to Traditional Chinese guidelines with rule references
GUIDELINES: Dict[str, str] = {
    "harassment": "騷擾內容（規則 2.1）：請勿發布包含騷擾、威脅、貶低或歧視他人的內容。我們希望所有成員都能在尊重與包容的環境中交流。",
    
    "harassment/threatening": "威脅性騷擾（規則 2.1）：發布威脅他人安全、隱私或尊嚴的內容是嚴格禁止的。包括任何形式的恐嚇或施壓他人的言論。",
    
    "hate": "仇恨言論（規則 2.2）：禁止任何基於種族、民族、宗教、性別、性取向、年齡、殘疾或其他個人特徵的仇恨、歧視或偏見言論。我們致力於建立一個平等和包容的社群。",
    
    "hate/threatening": "威脅性仇恨言論（規則 2.2）：特別針對特定群體的威脅性言論是嚴格禁止的。這包括任何形式的煽動暴力或歧視的內容。",
    
    "self-harm": "自我傷害相關內容（規則 2.6）：禁止分享鼓勵、美化或詳細描述自我傷害的內容。我們關心每一位成員的福祉，並鼓勵尋求專業協助。",
    
    "self-harm/intent": "自我傷害意圖（規則 2.6）：表達自我傷害意圖的內容是禁止的。若您或您認識的人正在經歷危機，請尋求專業協助或聯繫緊急熱線。",
    
    "self-harm/instructions": "自我傷害指導（規則 2.6）：禁止提供關於如何進行自我傷害的詳細指導或方法。這類內容可能對易受影響的個體造成嚴重傷害。",
    
    "sexual": "性相關內容（規則 2.3）：禁止分享露骨的色情內容、不適當的性暗示或任何可能冒犯他人的性相關討論。請保持對話適合所有年齡層。",
    
    "sexual/minors": "未成年相關性內容（規則 2.3）：嚴格禁止任何涉及未成年人的性相關內容。此類內容違反法律法規，將立即刪除並採取嚴厲措施。",
    
    "violence": "暴力內容（規則 2.3）：禁止分享過度暴力、鼓勵暴力行為或美化暴力的內容。我們希望維持一個和平且安全的交流環境。",
    
    "violence/graphic": "圖像化暴力內容（規則 2.3）：禁止分享包含血腥、殘忍或圖像化暴力的內容，這包括文字描述和視覺媒體。",
    
    "illicit": "不法行為（規則 2.7）：禁止討論、促進或提供關於非法活動的具體指導。這包括但不限於毒品交易、盜竊或欺詐等活動。",
    
    "illicit/violent": "暴力不法行為（規則 2.7）：特別禁止討論涉及暴力的非法活動，包括但不限於恐怖主義、組織犯罪或武器製造等相關內容。",
    
    "harassment_threatening": "威脅性騷擾（規則 2.1）：發布威脅他人安全、隱私或尊嚴的內容是嚴格禁止的。包括任何形式的恐嚇或施壓他人的言論。",
    "hate_threatening": "威脅性仇恨言論（規則 2.2）：特別針對特定群體的威脅性言論是嚴格禁止的。這包括任何形式的煽動暴力或歧視的內容。",
    "self_harm": "自我傷害相關內容（規則 2.6）：禁止分享鼓勵、美化或詳細描述自我傷害的內容。我們關心每一位成員的福祉，並鼓勵尋求專業協助。",
    "self_harm_intent": "自我傷害意圖（規則 2.6）：表達自我傷害意圖的內容是禁止的。若您或您認識的人正在經歷危機，請尋求專業協助或聯繫緊急熱線。",
    "self_harm_instructions": "自我傷害指導（規則 2.6）：禁止提供關於如何進行自我傷害的詳細指導或方法。這類內容可能對易受影響的個體造成嚴重傷害。",
    "sexual_minors": "未成年相關性內容（規則 2.3）：嚴格禁止任何涉及未成年人的性相關內容。此類內容違反法律法規，將立即刪除並採取嚴厲措施。",
    "violence_graphic": "圖像化暴力內容（規則 2.3）：禁止分享包含血腥、殘忍或圖像化暴力的內容，這包括文字描述和視覺媒體。",
    "illicit_violent": "暴力不法行為（規則 2.7）：特別禁止討論涉及暴力的非法活動，包括但不限於恐怖主義、組織犯罪或武器製造等相關內容。",
    "privacy": "隱私侵犯（規則 2.4）：未經許可分享他人的個人信息是嚴格禁止的。尊重所有成員的隱私權。",
    "spam": "垃圾訊息（規則 2.5）：禁止發送垃圾訊息、重複內容、無關廣告或過度標記他人。",
    "malware": "惡意軟體（規則 2.8）：禁止分享惡意軟體、病毒或其他具有潛在危害的檔案。",
    "phishing": "釣魚詐騙（規則 2.8）：禁止分享釣魚網站或其他詐騙連結，這類內容可能危害社群成員的網路安全。"
}

# Short version of guidelines for each category (used in notifications)
SHORT_GUIDELINES: Dict[str, str] = {
    "harassment": "禁止騷擾他人或發布冒犯性內容（規則 2.1）",
    "harassment/threatening": "禁止威脅或恐嚇他人（規則 2.1）",
    "hate": "禁止發布仇恨言論或歧視內容（規則 2.2）",
    "hate/threatening": "禁止發布威脅性的仇恨言論（規則 2.2）",
    "self-harm": "禁止分享自我傷害相關內容（規則 2.6）",
    "self-harm/intent": "禁止表達自我傷害的意圖（規則 2.6）",
    "self-harm/instructions": "禁止提供自我傷害的方法或指導（規則 2.6）",
    "sexual": "禁止分享不適當的性相關內容（規則 2.3）",
    "sexual/minors": "嚴禁分享涉及未成年人的性相關內容（規則 2.3）",
    "violence": "禁止分享或鼓勵暴力內容（規則 2.3）",
    "violence/graphic": "禁止分享圖像化的暴力內容（規則 2.3）",
    "illicit": "禁止討論或促進非法活動（規則 2.7）",
    "illicit/violent": "禁止討論涉及暴力的非法活動（規則 2.7）",
    "harassment_threatening": "禁止威脅或恐嚇他人（規則 2.1）",
    "hate_threatening": "禁止發布威脅性的仇恨言論（規則 2.2）",
    "self_harm": "禁止分享自我傷害相關內容（規則 2.6）",
    "self_harm_intent": "禁止表達自我傷害的意圖（規則 2.6）",
    "self_harm_instructions": "禁止提供自我傷害的方法或指導（規則 2.6）",
    "sexual_minors": "嚴禁分享涉及未成年人的性相關內容（規則 2.3）",
    "violence_graphic": "禁止分享圖像化的暴力內容（規則 2.3）",
    "illicit_violent": "禁止討論涉及暴力的非法活動（規則 2.7）",
    "privacy": "禁止侵犯他人隱私（規則 2.4）",
    "spam": "禁止發送垃圾訊息或過度標記他人（規則 2.5）",
    "malware": "禁止分享惡意軟體或病毒（規則 2.8）",
    "phishing": "禁止分享釣魚網站或詐騙連結（規則 2.8）"
}

# General community guidelines introduction with reference to the detailed document
COMMUNITY_GUIDELINES_INTRO = """
# HackIt社群規範

我們致力於創建一個友善、包容且積極的社群環境，讓所有成員都能安心地交流和學習。為了維護這一環境，我們制定了以下社群規範，所有成員都必須遵守。

完整的社群規範可在 `docs/community_guidelines_comprehensive.md` 查看，以下為摘要：

## 1. 基本原則

1.1 **尊重他人**：對所有社群成員保持尊重，不論其背景、觀點或經驗水平如何。
1.2 **建設性交流**：提供建設性的反饋和意見，避免無意義的批評。
1.3 **真誠互助**：鼓勵互相幫助，對新成員保持耐心和包容。
1.4 **共同責任**：每位成員都有責任維護社群秩序。

## 2. 禁止行為

以下行為在我們的社群中是嚴格禁止的：
"""

# Full community guidelines document (all in one)
def get_full_guidelines() -> str:
    """Get the full community guidelines document in Traditional Chinese."""
    full_guidelines = COMMUNITY_GUIDELINES_INTRO
    
    # Add all the detailed guidelines
    for category, guideline in GUIDELINES.items():
        full_guidelines += f"\n- **{guideline}**"
    
    # Add enforcement section
    full_guidelines += """

## 規範執行

違反上述規範可能導致以下後果，視情節嚴重程度而定：

1. **第一次違規**：警告並暫時禁言 5 分鐘
2. **第二次違規**：暫時禁言 12 小時
3. **第三次違規**：暫時禁言 7 天
4. **第四次違規**：暫時禁言 7 天
5. **第五次違規或以上**：暫時禁言 28 天

工作人員和版主有權根據具體情況執行這些措施，以維護社群安全和健康的交流環境。

詳細規範請查看 `docs/community_guidelines_comprehensive.md`。

我們感謝所有成員對維護積極社群環境的貢獻。如有任何問題或疑慮，請聯繫工作人員或版主。
"""
    
    return full_guidelines

def get_guidelines_for_violations(violation_categories: List[str]) -> List[str]:
    """
    Get relevant guidelines for specific violation categories.
    
    Args:
        violation_categories: List of violation category keys
        
    Returns:
        List of relevant guideline texts
    """
    return [SHORT_GUIDELINES.get(category, "違反社群規範") for category in violation_categories]

def format_mute_reason(violation_count: int, violation_categories: List[str]) -> str:
    """
    Format the mute reason based on violation count and categories.
    
    Args:
        violation_count: Number of violations
        violation_categories: List of violation category keys
        
    Returns:
        Formatted mute reason text
    """
    # 獲取簡短違規原因，每條保持在15字以內
    short_guidelines = []
    for category in violation_categories:
        guideline = SHORT_GUIDELINES.get(category, "違反社群規範")
        # 從括號之前擷取內容，確保簡短
        if "（" in guideline:
            short_guideline = guideline.split("（")[0]
        else:
            short_guideline = guideline
        short_guidelines.append(short_guideline)
    
    # 創建簡短的違規原因列表
    guidelines_text = "\n".join([f"- {guideline}" for guideline in short_guidelines])
    
    # 根據違規次數給出簡短的禁言時間說明
    if violation_count == 1:
        reason = f"第一次違規：5分鐘禁言\n違規原因：\n{guidelines_text}"
    elif violation_count == 2:
        reason = f"第二次違規：12小時禁言\n違規原因：\n{guidelines_text}"
    elif violation_count == 3:
        reason = f"第三次違規：7天禁言\n違規原因：\n{guidelines_text}"
    elif violation_count == 4:
        reason = f"第四次違規：7天禁言\n違規原因：\n{guidelines_text}"
    else:
        reason = f"第五次違規：28天禁言\n違規原因：\n{guidelines_text}"
    
    # 添加簡短的申訴提示
    reason += "\n\n如需申訴請聯繫工作人員。"
    
    return reason 