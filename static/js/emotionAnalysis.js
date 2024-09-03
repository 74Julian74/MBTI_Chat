const emotionAnalysis = {
    getCsrfToken: function() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : null;
    },

    analyzeEmotion: async function(groupId) {
        try {
            const csrfToken = this.getCsrfToken();
            if (!csrfToken) {
                throw new Error('CSRF token not found');
            }

            const replyStyleSelect = document.getElementById('reply-style-select');
            const replyStyle = replyStyleSelect ? replyStyleSelect.value : '正式';
            console.log('Sending analysis request with reply style:', replyStyle); // 添加日誌
            
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
            return null;
        }
    },

    updateAnalysisUI: function(analysis) {
        console.log('Updating UI with analysis:', analysis);
        if (analysis) {
            this.updateElement('#person-name', analysis.name || 'Unknown');
            this.updateElement('#person-mbti', analysis.mbti || 'Unknown');
            this.updateElement('#person-emotion', analysis.emotion || 'Unknown');
            
            if (analysis.suggestions && Array.isArray(analysis.suggestions) && analysis.suggestions.length >= 2) {
                document.getElementById('suggestion-1').value = analysis.suggestions[0] || '';
                document.getElementById('suggestion-2').value = analysis.suggestions[1] || '';
            } else {
                document.getElementById('suggestion-1').value = '無可用建議';
                document.getElementById('suggestion-2').value = '無可用建議';
            }
            document.getElementById('analysis-error').textContent = '';
        } else {
            console.error('No analysis data received');
            document.getElementById('analysis-error').textContent = '無法獲取分析數據';
            this.updateElement('#person-name', 'Unknown');
            this.updateElement('#person-mbti', 'Unknown');
            this.updateElement('#person-emotion', 'Unknown');
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

document.addEventListener('DOMContentLoaded', function() {
    const button = document.querySelector('#emotion-analysis-button');
    if (button) {
        button.addEventListener('click', async function() {
            const groupId = 'default_group'; // 替換為實際的群組 ID 邏輯
            const analysis = await emotionAnalysis.analyzeEmotion(groupId);
            emotionAnalysis.updateAnalysisUI(analysis);
        });
    } else {
        console.error("找不到 id 為 'emotion-analysis-button' 的按鈕元素");
    }
});