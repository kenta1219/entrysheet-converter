// ファイル変換Webアプリ - JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const loading = document.getElementById('loading');
    const loadingText = document.getElementById('loadingText');
    const success = document.getElementById('success');
    const successText = document.getElementById('successText');
    const error = document.getElementById('error');
    const errorText = document.getElementById('errorText');

    // フォーム送信イベント
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // UI状態をリセット
        hideAllMessages();
        
        // ボタンを無効化し、ローディング表示
        submitBtn.disabled = true;
        loading.style.display = 'block';
        loadingText.textContent = 'ファイルを処理中です...';
        
        // FormDataを作成してファイルを送信
        const formData = new FormData(this);
        
        fetch('/process', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                // 成功時の処理
                loadingText.textContent = '処理が完了しました！ダウンロードを開始します...';
                
                // ファイルダウンロード
                return response.blob().then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    
                    // フォルダ構造付きのファイル名を生成
                    const filename = generateDownloadPath();
                    a.download = filename;
                    
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    // 成功メッセージを表示
                    showSuccess('処理が完了しました！ファイルがダウンロードされました。');
                });
            } else {
                // エラーレスポンスの処理
                return response.text().then(text => {
                    let errorMessage = 'ファイル処理に失敗しました。';
                    try {
                        const errorData = JSON.parse(text);
                        if (errorData.detail) {
                            errorMessage = errorData.detail;
                        }
                    } catch (e) {
                        // JSONパースに失敗した場合はデフォルトメッセージを使用
                    }
                    throw new Error(errorMessage);
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError(error.message || 'エラーが発生しました。再度お試しください。');
        });
    });

    // ファイル選択時のバリデーション
    const xlsbFile = document.getElementById('xlsb_file');
    const templateFile = document.getElementById('template_file');
    
    xlsbFile.addEventListener('change', function() {
        validateFile(this, ['.xlsb'], 'xlsbファイル');
    });
    
    templateFile.addEventListener('change', function() {
        validateFile(this, ['.xlsx', '.xlsm'], 'テンプレートファイル');
    });

    // ヘルパー関数
    function hideAllMessages() {
        loading.style.display = 'none';
        success.style.display = 'none';
        error.style.display = 'none';
    }

    function showSuccess(message) {
        hideAllMessages();
        successText.textContent = message;
        success.style.display = 'block';
        
        // 5秒後にリセット
        setTimeout(() => {
            resetForm();
        }, 5000);
    }

    function showError(message) {
        hideAllMessages();
        errorText.textContent = message;
        error.style.display = 'block';
        submitBtn.disabled = false;
        
        // 8秒後にエラーメッセージを非表示
        setTimeout(() => {
            error.style.display = 'none';
        }, 8000);
    }

    function resetForm() {
        submitBtn.disabled = false;
        hideAllMessages();
        loadingText.textContent = 'ファイルを処理中です...';
    }

    function validateFile(input, allowedExtensions, fileType) {
        const file = input.files[0];
        if (!file) return;

        // ファイル拡張子チェック
        const fileName = file.name.toLowerCase();
        const isValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
        
        if (!isValidExtension) {
            showError(`${fileType}は${allowedExtensions.join(', ')}形式のファイルを選択してください。`);
            input.value = '';
            return;
        }

        // ファイルサイズチェック (10MB)
        const maxSize = 10 * 1024 * 1024; // 10MB in bytes
        if (file.size > maxSize) {
            showError(`ファイルサイズは10MB以下にしてください。選択されたファイル: ${(file.size / 1024 / 1024).toFixed(2)}MB`);
            input.value = '';
            return;
        }
    }

    // ドラッグ&ドロップ機能（オプション）
    function setupDragAndDrop() {
        const container = document.querySelector('.container');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            container.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            container.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            container.addEventListener(eventName, unhighlight, false);
        });

        function highlight() {
            container.classList.add('drag-over');
        }

        function unhighlight() {
            container.classList.remove('drag-over');
        }

        container.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                // 最初のファイルを適切な入力フィールドに設定
                const file = files[0];
                const fileName = file.name.toLowerCase();
                
                if (fileName.endsWith('.xlsb')) {
                    xlsbFile.files = files;
                    validateFile(xlsbFile, ['.xlsb'], 'xlsbファイル');
                } else if (fileName.endsWith('.xlsx') || fileName.endsWith('.xlsm')) {
                    templateFile.files = files;
                    validateFile(templateFile, ['.xlsx', '.xlsm'], 'テンプレートファイル');
                }
            }
        }
    }

    // ドラッグ&ドロップ機能を初期化
    setupDragAndDrop();

    // フォルダ構造付きファイル名を生成
    function generateDownloadPath() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const dateFolder = `${year}${month}${day}`;
        
        const filename = window.OUTPUT_FILENAME || '店子申請_転記済.xlsx';
        return `AEON_電子マネー/${dateFolder}/${filename}`;
    }
});