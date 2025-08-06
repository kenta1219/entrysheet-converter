// 一括処理Webアプリ - JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // 要素の取得
    const batchForm = document.getElementById('batchForm');
    const batchSubmitBtn = document.getElementById('batchSubmitBtn');
    const facilityNameInput = document.getElementById('facility_name');
    const zipFilenamePreview = document.getElementById('zipFilenamePreview');
    const loading = document.getElementById('loading');
    const loadingText = document.getElementById('loadingText');
    const success = document.getElementById('success');
    const successText = document.getElementById('successText');
    const error = document.getElementById('error');
    const errorText = document.getElementById('errorText');
    
    // ファイル名プレビューを更新
    updateFilenamePreview();
    
    // 既存のチェックボックスにイベントリスナーを追加
    setupExistingCheckboxes();

    // 一括処理フォーム送信イベント（Ajaxベース）
    if (batchForm) {
        batchForm.addEventListener('submit', function(e) {
            e.preventDefault(); // フォーム送信を停止
            
            const facilityName = facilityNameInput.value.trim();
            const checkedBoxes = document.querySelectorAll('input[name="selected_templates"]:checked');
            const xlsbFileInput = document.getElementById('batch_xlsb_file');
            
            // フォームバリデーション
            if (!facilityName) {
                showBatchError('施設名を入力してください。');
                return;
            }
            
            if (checkedBoxes.length === 0) {
                showBatchError('処理対象のテンプレートを選択してください。');
                return;
            }
            
            if (!xlsbFileInput.files[0]) {
                showBatchError('xlsbファイルを選択してください。');
                return;
            }
            
            // ローディング表示
            batchSubmitBtn.disabled = true;
            loading.style.display = 'block';
            loadingText.textContent = '一括処理を実行中です...';
            
            // FormDataを作成
            const formData = new FormData();
            formData.append('facility_name', facilityName);
            formData.append('xlsb_file', xlsbFileInput.files[0]);
            
            // 選択されたテンプレートを追加
            checkedBoxes.forEach(checkbox => {
                formData.append('selected_templates', checkbox.value);
            });
            
            // Ajax送信
            fetch('/batch-process', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    // 成功時はファイルダウンロード
                    return response.blob().then(blob => {
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.style.display = 'none';
                        a.href = url;
                        
                        // Content-Dispositionヘッダーからファイル名を取得（日本語対応）
                        const contentDisposition = response.headers.get('Content-Disposition');
                        let filename = 'batch_processed_templates.zip';

                        if (contentDisposition) {
                            const filenameStarMatch = contentDisposition.match(/filename\*=UTF-8''([^;\n]*)/);
                            const filenameMatch = contentDisposition.match(/filename="([^"]+)"/);

                            if (filenameStarMatch) {
                                try {
                                    filename = decodeURIComponent(filenameStarMatch[1]);
                                } catch (e) {
                                    console.warn('ファイル名のデコードに失敗しました', e);
                                }
                            } else if (filenameMatch) {
                                filename = filenameMatch[1];
                            }
                        }
                        
                        a.download = filename;
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                        
                        showBatchSuccess('一括処理が完了しました。ZIPファイルをダウンロードしています。');
                    });
                } else {
                    return response.text().then(text => {
                        let message = '一括処理中にエラーが発生しました。';
                        try {
                            const data = JSON.parse(text);
                            if (data && data.detail) {
                                message = data.detail;
                            }
                        } catch (e) {
                            console.warn('レスポンスはJSONではありません:', text);
                            message = text || message;
                        }
                        throw new Error(message);
                    });
                }
            })
            .catch(error => {
                console.error('一括処理エラー:', error);
                showBatchError(error.message || '一括処理中にエラーが発生しました。');
            });
        });
    }

    // ファイル選択時のバリデーション
    const xlsbFile = document.getElementById('batch_xlsb_file');
    
    if (xlsbFile) {
        xlsbFile.addEventListener('change', function() {
            validateFile(this, ['.xlsb'], 'xlsbファイル');
        });
    }

    // ヘルパー関数
    function hideAllMessages() {
        loading.style.display = 'none';
        success.style.display = 'none';
        error.style.display = 'none';
    }

    function showBatchSuccess(message) {
        hideAllMessages();
        successText.textContent = message;
        success.style.display = 'block';
        batchSubmitBtn.disabled = false;
        
        // 5秒後にリセット
        setTimeout(() => {
            resetBatchForm();
        }, 5000);
    }

    function showBatchError(message) {
        hideAllMessages();
        errorText.textContent = message;
        error.style.display = 'block';
        batchSubmitBtn.disabled = false;
        
        // 8秒後にエラーメッセージを非表示
        setTimeout(() => {
            error.style.display = 'none';
        }, 8000);
    }

    function resetBatchForm() {
        batchSubmitBtn.disabled = false;
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
            showBatchError(`${fileType}は${allowedExtensions.join(', ')}形式のファイルを選択してください。`);
            input.value = '';
            return;
        }

        // ファイルサイズチェック (10MB)
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            showBatchError(`${fileType}のサイズが大きすぎます。10MB以下のファイルを選択してください。`);
            input.value = '';
            return;
        }
    }

    // ファイル名プレビュー更新関数
    function updateFilenamePreview() {
        if (facilityNameInput && zipFilenamePreview) {
            facilityNameInput.addEventListener('input', function() {
                const facilityName = this.value.trim();
                const today = new Date();
                const dateStr = today.getFullYear() + 
                               String(today.getMonth() + 1).padStart(2, '0') + 
                               String(today.getDate()).padStart(2, '0');
                
                if (facilityName) {
                    zipFilenamePreview.textContent = `${facilityName}_${dateStr}.zip`;
                } else {
                    zipFilenamePreview.textContent = `施設名_${dateStr}.zip`;
                }
            });
        }
    }

    // 既存のチェックボックスにイベントリスナーを設定
    function setupExistingCheckboxes() {
        const checkboxes = document.querySelectorAll('input[name="selected_templates"]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                // 少なくとも1つはチェックされている状態を保つ
                const checkedBoxes = document.querySelectorAll('input[name="selected_templates"]:checked');
                if (checkedBoxes.length === 0) {
                    this.checked = true;
                    showBatchError('少なくとも1つのテンプレートを選択してください。');
                }
            });
        });
    }
});