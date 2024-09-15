const emotionAnalysis = {
    getCsrfToken: function() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : null;
    },

    analyzeEmotion: async function() {
        try {
            const csrfToken = this.getCsrfToken();
            if (!csrfToken) {
                throw new Error('CSRF token not found');
            }

            // 获取当前活动的群组ID
            const groupId = window.getCurrentGroupId(); // 假设这个函数存在于全局作用域
            if (!groupId) {
                throw new Error('No active chat group');
            }

            const replyStyleSelect = document.getElementById('reply-style-select');
            const replyStyle = replyStyleSelect ? replyStyleSelect.value : '正式';
            console.log('Sending analysis request for group:', groupId, 'with reply style:', replyStyle); // 添加日誌
            
            const response = await fetch('/analyze_emotion', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ 
                    group_id: groupId,
                    reply_style: replyStyle
                })
            });
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const result = await response.json();
            console.log('Received analysis result:', result);
            return result;
        } catch (error) {
            console.error('分析情緒時出錯：', error);
            return {
                error: true,
                message: error.message || '未知錯誤'
            };
        }
    },

    updateAnalysisUI: function(analysis) {
        console.log('Updating UI with analysis:', analysis);
        if (analysis && !analysis.error) {
            this.updateElement('#person-name', analysis.name || 'Unknown');
            this.updateElement('#person-mbti', analysis.mbti || 'Unknown');
            this.updateElement('#person-emotion', analysis.emotion || 'Unknown');
            this.updateElement('#emotion-reason', analysis.emotion_reason || 'Unknown');
            
            // 更新MBTI解釋
            const mbtiExplanationElement = document.getElementById('mbti-explanation');
            if (mbtiExplanationElement && analysis.mbti_explanation) {
                mbtiExplanationElement.innerHTML = analysis.mbti_explanation.replace(/\n/g, '<br>');
            } else {
                mbtiExplanationElement.innerHTML = '無MBTI解釋';
            }
            
            if (analysis.suggestions && Array.isArray(analysis.suggestions) && analysis.suggestions.length >= 2) {
                document.getElementById('suggestion-1').value = analysis.suggestions[0] || '';
                document.getElementById('suggestion-2').value = analysis.suggestions[1] || '';
            } else {
                document.getElementById('suggestion-1').value = '無可用建議';
                document.getElementById('suggestion-2').value = '無可用建議';
            }
            document.getElementById('analysis-error').textContent = '';
        } else {
            console.error('Analysis error or no data received:', analysis);
            document.getElementById('analysis-error').textContent = analysis.message || '無法獲取分析數據';
            this.updateElement('#person-name', 'Unknown');
            this.updateElement('#person-mbti', 'Unknown');
            this.updateElement('#person-emotion', 'Unknown');
            this.updateElement('#emotion-reason', 'Unknown');
            document.getElementById('mbti-explanation').innerHTML = '';
            document.getElementById('suggestion-1').value = '';
            document.getElementById('suggestion-2').value = '';
        }
    },

    updateElement: function(selector, text) {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = text;
        } else {
            console.error(`Element not found: ${selector}`);
        }
    }
};
// 添加一個新的函數來處理回覆建議的選擇
function selectSuggestion(suggestionNumber) {
    const suggestionText = document.getElementById(`suggestion-${suggestionNumber}`).value;
    const messageInput = document.getElementById('message-input');
    messageInput.value = suggestionText;
    messageInput.focus();
}