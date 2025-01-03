const emotionAnalysis = {
    getCsrfToken: function() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : null;
    },

    analyzeEmotion: async function() {
        const analyzeButton = document.getElementById('emotion-analysis-button');
        try {
            const csrfToken = this.getCsrfToken();
            if (!csrfToken) {
                throw new Error('找不到 CSRF token');
            }
    
            const groupId = window.getCurrentGroupId();
            if (!groupId) {
                throw new Error('請先選擇聊天對象');
            }
    
            const replyStyleSelect = document.getElementById('reply-style-select');
            const replyStyle = replyStyleSelect ? replyStyleSelect.value : '正式';
            
            // 設置按鈕狀態
            if (analyzeButton) {
                analyzeButton.disabled = true;
                analyzeButton.textContent = '分析中...';
            }
            
            console.log('發送分析請求:', { group_id: groupId, reply_style: replyStyle });
            
            const response = await fetch('/analyze_emotion', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ 
                    group_id: groupId,
                    reply_style: replyStyle
                })
            });
    
            const result = await response.json();
            console.log('收到分析結果:', result);
            
            if (!response.ok) {
                throw new Error(result.error || `請求失敗 (${response.status})`);
            }
    
            if (result.error) {
                throw new Error(result.error);
            }
    
            return result;
        } catch (error) {
            console.error('分析情緒時出錯：', error);
            document.getElementById('analysis-error').textContent = 
                error.message || '分析過程中發生錯誤，請稍後重試';
            return {
                error: true,
                message: error.message || '分析過程中發生錯誤，請稍後重試'
            };
        } finally {
            // 恢復按鈕狀態
            if (analyzeButton) {
                analyzeButton.disabled = false;
                analyzeButton.textContent = '情緒分析';
            }
        }
    },

    // 新增的回覆建議功能
    getReplySuggestions: async function() {
        const suggestButton = document.getElementById('reply-suggestion-button');
        try {
            const csrfToken = this.getCsrfToken();
            if (!csrfToken) {
                throw new Error('找不到 CSRF token');
            }
    
            const groupId = window.getCurrentGroupId();
            if (!groupId) {
                throw new Error('請先選擇聊天對象');
            }
    
            const replyStyleSelect = document.getElementById('reply-style-select');
            const replyStyle = replyStyleSelect ? replyStyleSelect.value : '正式';
            
            if (suggestButton) {
                suggestButton.disabled = true;
                suggestButton.textContent = '產生建議中...';
            }
            
            console.log('發送回覆建議請求:', { group_id: groupId, reply_style: replyStyle });
            
            const response = await fetch('/get_reply_suggestions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ 
                    group_id: groupId,
                    reply_style: replyStyle
                })
            });
    
            const result = await response.json();
            console.log('收到回覆建議結果:', result);
            
            if (!response.ok) {
                throw new Error(result.error || `請求失敗 (${response.status})`);
            }
    
            if (result.error) {
                throw new Error(result.error);
            }
    
            return result;
        } catch (error) {
            console.error('獲取回覆建議時出錯：', error);
            document.getElementById('analysis-error').textContent = 
                error.message || '獲取回覆建議時出錯，請稍後重試';
            return {
                error: true,
                message: error.message || '獲取回覆建議時出錯，請稍後重試'
            };
        } finally {
            if (suggestButton) {
                suggestButton.disabled = false;
                suggestButton.textContent = '回覆建議';
            }
        }
    },

    showLoading: function(isLoading) {
        const analyzeButton = document.getElementById('emotion-analysis-button');
        const suggestButton = document.getElementById('reply-suggestion-button');
        if (analyzeButton) {
            analyzeButton.disabled = isLoading;
            analyzeButton.textContent = isLoading ? '分析中...' : '情緒分析';
        }
        if (suggestButton) {
            suggestButton.disabled = isLoading;
            suggestButton.textContent = isLoading ? '產生建議中...' : '回覆建議';
        }
    },

    // 更新 UI 顯示，根據不同類型的結果顯示不同內容
    updateAnalysisUI: function(analysis, type = 'emotion') {
        if (analysis && !analysis.error) {
            // 清空錯誤信息
            const errorElement = document.getElementById('analysis-error');
            if (errorElement) {
                errorElement.textContent = '';
            }

            if (type === 'emotion') {
                // 更新用戶信息
                const nameElement = document.getElementById('person-name');
                const mbtiElement = document.getElementById('person-mbti');
                if (nameElement) nameElement.textContent = analysis.name || 'Unknown';
                if (mbtiElement) mbtiElement.textContent = analysis.mbti || 'Unknown';
                
                // 更新當前情緒
                const personEmotion = document.getElementById('person-emotion');
                if (personEmotion && analysis.emotion_name) {
                    personEmotion.textContent = analysis.person_emotion || 'Unknown';
                }

                // 更新情緒分析結果
                if (analysis.emotions) {
                    for (const [emotion, score] of Object.entries(analysis.emotions)) {
                        const element = document.getElementById(`${emotion}-score`);
                        if (element) {
                            element.textContent = `${(score * 100).toFixed(1)}%`;
                        }
                    }
                }

                // 更新 MBTI 解釋
                const mbtiExplanationElement = document.getElementById('mbti-explanation');
                if (mbtiExplanationElement && analysis.mbti_explanation) {
                    mbtiExplanationElement.innerHTML = analysis.mbti_explanation.replace(/\n/g, '<br>');
                }
            } else if (type === 'suggestions') {
                // 更新建議回復
                const suggestion1 = document.getElementById('suggestion-1');
                const suggestion2 = document.getElementById('suggestion-2');
                
                if (suggestion1 && suggestion2 && analysis.suggestions && analysis.suggestions.length >= 2) {
                    suggestion1.value = analysis.suggestions[0];
                    suggestion2.value = analysis.suggestions[1];
                }
            }
        } else {
            // 處理錯誤情況
            const errorElement = document.getElementById('analysis-error');
            if (errorElement) {
                errorElement.textContent = analysis.message || '無法獲取分析數據';
            }
        }
    },

    clearAllFields: function() {
        this.updateElement('#person-name', '');
        this.updateElement('#person-mbti', '');
        
        const emotions = ['anger', 'disgust', 'fear', 'sadness', 'surprise', 'happiness'];
        emotions.forEach(emotion => {
            const element = document.getElementById(`${emotion}-score`);
            if (element) {
                element.textContent = '0%';
            }
        });

        const mbtiExplanation = document.getElementById('mbti-explanation');
        if (mbtiExplanation) {
            mbtiExplanation.innerHTML = '';
        }

        const suggestion1 = document.getElementById('suggestion-1');
        const suggestion2 = document.getElementById('suggestion-2');
        if (suggestion1) suggestion1.value = '';
        if (suggestion2) suggestion2.value = '';
    },

    updateElement: function(selector, text) {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = text;
        }
    }
};

// 初始化事件監聽
document.addEventListener('DOMContentLoaded', function() {
    const analyzeButton = document.getElementById('emotion-analysis-button');
    const suggestionButton = document.getElementById('reply-suggestion-button');

    if (analyzeButton) {
        analyzeButton.addEventListener('click', async function() {
            try {
                if (!window.getCurrentGroupId()) {
                    document.getElementById('analysis-error').textContent = '請先選擇聊天對象';
                    return;
                }
                
                const analysis = await emotionAnalysis.analyzeEmotion();
                emotionAnalysis.updateAnalysisUI(analysis, 'emotion');
            } catch (error) {
                console.error('情緒分析失敗:', error);
                document.getElementById('analysis-error').textContent = 
                    error.message || '情緒分析失敗，請稍後重試';
            }
        });
    }

    if (suggestionButton) {
        suggestionButton.addEventListener('click', async function() {
            try {
                if (!window.getCurrentGroupId()) {
                    document.getElementById('analysis-error').textContent = '請先選擇聊天對象';
                    return;
                }
                
                const suggestions = await emotionAnalysis.getReplySuggestions();
                emotionAnalysis.updateAnalysisUI(suggestions, 'suggestions');
            } catch (error) {
                console.error('獲取回覆建議失敗:', error);
                document.getElementById('analysis-error').textContent = 
                    error.message || '獲取回覆建議失敗，請稍後重試';
            }
        });
    }
});