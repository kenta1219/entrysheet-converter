// エントリーシート変換アプリ - JavaScript (v3.0)

document.addEventListener('DOMContentLoaded', function() {
    // 共通要素の取得
    const loading = document.getElementById('loading');
    const loadingText = document.getElementById('loadingText');
    const success = document.getElementById('success');
    const successText = document.getElementById('successText');
    const error = document.getElementById('error');
    const errorText = document.getElementById('errorText');
    
    // 機能選択の初期化
    initializeFeatureSelector();
    
    // 従来機能の初期化
    initializeBatchProcessing();
    
    // 複数ファイル処理機能の初期化
    initializeMultiFileProcessing();
    
    // 機能選択の初期化
    function initializeFeatureSelector() {
        const modeCards = document.querySelectorAll('.mode-card');
        const selectButtons = document.querySelectorAll('.select-mode-btn');
        
        selectButtons.forEach(button => {
            button.addEventListener('click', function() {
                const targetMode = this.dataset.target;
                showProcessingForm(targetMode);
            });
        });
    }
    
    // 処理フォームを表示
    function showProcessingForm(mode) {
        // 機能選択を非表示
        document.getElementById('featureSelector').style.display = 'none';
        
        // 全フォームを非表示
        document.getElementById('batch-processing-form').style.display = 'none';
        document.getElementById('multi-file-processing-form').style.display = 'none';
        
        // 選択されたフォームを表示
        if (mode === 'batch') {
            document.getElementById('batch-processing-form').style.display = 'block';
        } else if (mode === 'multi-file') {
            document.getElementById('multi-file-processing-form').style.display = 'block';
        }
        
        // 戻るボタンを追加
        addBackButton();
    }
    
    // 戻るボタンを追加
    function addBackButton() {
        const existingBackBtn = document.getElementById('backToSelector');
        if (existingBackBtn) return;
        
        const backButton = document.createElement('button');
        backButton.id = 'backToSelector';
        backButton.type = 'button';
        backButton.className = 'back-btn';
        backButton.innerHTML = '← 機能選択に戻る';
        backButton.addEventListener('click', function() {
            document.getElementById('featureSelector').style.display = 'block';
            document.getElementById('batch-processing-form').style.display = 'none';
            document.getElementById('multi-file-processing-form').style.display = 'none';
            hideAllMessages();
            this.remove();
        });
        
        document.querySelector('.container').insertBefore(backButton, document.querySelector('.processing-form'));
    }
    
    // 従来機能の初期化
    function initializeBatchProcessing() {
        const batchForm = document.getElementById('batchForm');
        const batchSubmitBtn = document.getElementById('batchSubmitBtn');
        const facilityNameInput = document.getElementById('facility_name');
        const zipFilenamePreview = document.getElementById('zipFilenamePreview');
        
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
    }
    
    // 複数ファイル処理機能の初期化
    function initializeMultiFileProcessing() {
        const multiFileForm = document.getElementById('multiFileForm');
        const multiFileSubmitBtn = document.getElementById('multiFileSubmitBtn');
        const xlsbFilesInput = document.getElementById('xlsb_files');
        const multiFileDropZone = document.getElementById('multiFileDropZone');
        const selectedFilesList = document.getElementById('selectedFilesList');
        const facilityNamesContainer = document.getElementById('facilityNamesContainer');
        
        let selectedFiles = [];
        const maxFiles = 20;
        
        // ファイル選択イベント
        if (xlsbFilesInput) {
            xlsbFilesInput.addEventListener('change', function(e) {
                const files = Array.from(e.target.files);
                processSelectedFiles(files);
            });
        }
        
        // ドラッグ&ドロップ対応
        if (multiFileDropZone) {
            multiFileDropZone.addEventListener('dragover', function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.classList.add('drag-over');
            });
            
            multiFileDropZone.addEventListener('dragleave', function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.classList.remove('drag-over');
            });
            
            multiFileDropZone.addEventListener('drop', function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.classList.remove('drag-over');
                
                const files = Array.from(e.dataTransfer.files);
                processSelectedFiles(files);
                
                // input要素にもファイルを設定
                const dataTransfer = new DataTransfer();
                files.forEach(file => dataTransfer.items.add(file));
                xlsbFilesInput.files = dataTransfer.files;
            });
            
            // クリックでファイル選択
            multiFileDropZone.addEventListener('click', function(e) {
                if (e.target === this || e.target.classList.contains('drop-zone-content') || e.target.classList.contains('upload-icon')) {
                    xlsbFilesInput.click();
                }
            });
        }
        
        // 複数ファイル処理フォーム送信
        if (multiFileForm) {
            multiFileForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                if (selectedFiles.length === 0) {
                    showError('ファイルを選択してください。');
                    return;
                }
                
                const targetTemplate = document.getElementById('target_template').value;
                
                if (!targetTemplate) {
                    showError('出力先テンプレートを選択してください。');
                    return;
                }
                
                // FormDataを作成
                const formData = new FormData();
                selectedFiles.forEach(file => {
                    formData.append('xlsb_files', file);
                });
                formData.append('target_template', targetTemplate);
                
                // 送信処理
                await submitMultiFileForm(formData);
            });
        }
        
        // ファイル処理関数
        function processSelectedFiles(files) {
            // ファイル数制限チェック
            if (files.length > maxFiles) {
                showError(`最大${maxFiles}ファイルまで選択可能です。`);
                return;
            }
            
            // xlsb形式チェック
            const invalidFiles = files.filter(file => !file.name.toLowerCase().endsWith('.xlsb'));
            if (invalidFiles.length > 0) {
                showError('xlsb形式のファイルのみ選択してください。');
                return;
            }
            
            selectedFiles = files;
            updateFilesList();
        }
        
        // ファイルリスト表示更新
        function updateFilesList() {
            if (!selectedFilesList) return;
            
            selectedFilesList.innerHTML = '';
            
            if (selectedFiles.length === 0) {
                selectedFilesList.innerHTML = '<p class="no-files">ファイルが選択されていません</p>';
                return;
            }
            
            const fileList = document.createElement('div');
            fileList.className = 'file-list';
            
            selectedFiles.forEach((file, index) => {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                fileItem.innerHTML = `
                    <span class="file-name">${file.name}</span>
                    <span class="file-size">(${formatFileSize(file.size)})</span>
                    <button type="button" class="remove-file-btn" data-index="${index}">×</button>
                `;
                fileList.appendChild(fileItem);
            });
            
            selectedFilesList.appendChild(fileList);
            
            // ファイル削除ボタンのイベントリスナー
            selectedFilesList.querySelectorAll('.remove-file-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const index = parseInt(e.target.dataset.index);
                    removeFile(index);
                });
            });
        }
        
        // ファイル削除
        function removeFile(index) {
            selectedFiles.splice(index, 1);
            updateFilesList();
        }
        
        
        // 複数ファイル処理送信
        async function submitMultiFileForm(formData) {
            const btnText = multiFileSubmitBtn.querySelector('.btn-text');
            const btnLoading = multiFileSubmitBtn.querySelector('.btn-loading');
            
            try {
                // ローディング状態に変更
                multiFileSubmitBtn.disabled = true;
                btnText.style.display = 'none';
                btnLoading.style.display = 'inline-flex';
                loading.style.display = 'block';
                loadingText.textContent = '複数ファイルを処理中です...';
                
                const response = await fetch('/multi-file-process', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    // ファイルダウンロード処理
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = getDownloadFilename(response);
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                    
                    showSuccess('一括集約処理が完了しました！');
                } else {
                    const errorData = await response.json();
                    showError(`エラー: ${errorData.detail}`);
                }
            } catch (error) {
                showError(`処理中にエラーが発生しました: ${error.message}`);
            } finally {
                // ローディング状態を解除
                multiFileSubmitBtn.disabled = false;
                btnText.style.display = 'inline';
                btnLoading.style.display = 'none';
                loading.style.display = 'none';
            }
        }
        
        // ダウンロードファイル名取得
        function getDownloadFilename(response) {
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'multi_file_processed.xlsx';
            
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
            
            return filename;
        }
        
        // ファイルサイズフォーマット
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
    }
    
    // 共通メッセージ表示関数
    function hideAllMessages() {
        loading.style.display = 'none';
        success.style.display = 'none';
        error.style.display = 'none';
    }
    
    function showSuccess(message) {
        hideAllMessages();
        successText.textContent = message;
        success.style.display = 'block';
        
        setTimeout(() => {
            success.style.display = 'none';
        }, 5000);
    }
    
    function showError(message) {
        hideAllMessages();
        errorText.textContent = message;
        error.style.display = 'block';
        
        setTimeout(() => {
            error.style.display = 'none';
        }, 8000);
    }
});