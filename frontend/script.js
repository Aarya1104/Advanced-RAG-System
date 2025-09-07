document.addEventListener('DOMContentLoaded', () => {
    // Element selectors
    const queryForm = document.getElementById('query-form');
    const fileInput = document.getElementById('file-input');
    const fileNameDisplay = document.getElementById('file-name-display');
    const uploadButton = document.getElementById('upload-button');
    const queryInput = document.getElementById('query-input');
    const pasteInput = document.getElementById('paste-input');
    const pasteButton = document.getElementById('paste-button');
    const statusMessage = document.getElementById('status-message');
    const answerEl = document.getElementById('answer');
    const sourcesContainer = document.getElementById('sources-container');
    const statsContainer = document.getElementById('stats-container');
    const loader = document.getElementById('loader');
    const docSelect = document.getElementById('doc-select');
    const errorBox = document.getElementById('error-message');

    // Helper Functions
    const displayError = (message) => {
        errorBox.textContent = message;
        errorBox.style.display = 'block';
    };

    const clearAllOutputs = () => {
        statusMessage.textContent = 'Your results will appear here.';
        statusMessage.style.color = '#666';
        errorBox.style.display = 'none';
        answerEl.innerHTML = '';
        sourcesContainer.innerHTML = '';
        statsContainer.innerHTML = '';
        statsContainer.style.display = 'none';
    };

    const updateDocumentList = async () => {
        try {
            const response = await fetch('/api/documents');
            if (!response.ok) throw new Error('Failed to fetch document list.');
            const data = await response.json();

            while (docSelect.options.length > 1) docSelect.remove(1);

            data.documents.forEach(docName => {
                const option = document.createElement('option');
                option.value = docName;
                option.textContent = docName;
                docSelect.appendChild(option);
            });
        } catch (error) {
            displayError(error.message);
        }
    };

    // Event Listeners
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            fileNameDisplay.textContent = fileInput.files[0].name;
            fileNameDisplay.style.color = '#333';
        } else {
            fileNameDisplay.textContent = 'No file selected';
            fileNameDisplay.style.color = '#666';
        }
    });

    uploadButton.addEventListener('click', async () => {
        clearAllOutputs();
        const file = fileInput.files[0];
        if (!file) {
            displayError('Please select a file first.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        statusMessage.textContent = `Uploading '${file.name}'...`;
        statusMessage.style.color = 'orange';

        try {
            const response = await fetch('/api/upload', { method: 'POST', body: formData });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || 'Upload failed');

            statusMessage.textContent = result.message;
            statusMessage.style.color = 'green';
            updateDocumentList();
        } catch (error) {
            statusMessage.textContent = 'Upload failed.';
            statusMessage.style.color = 'red';
            displayError(error.message);
        } finally {
            fileInput.value = '';
            fileNameDisplay.textContent = 'No file selected';
        }
    });

    pasteButton.addEventListener('click', async () => {
        clearAllOutputs();
        const text = pasteInput.value;
        if (!text.trim()) {
            displayError('Please paste some text first.');
            return;
        }

        const filename = `Pasted Text - ${new Date().toLocaleString()}.txt`;
        statusMessage.textContent = `Processing pasted text...`;
        statusMessage.style.color = 'orange';

        try {
            const response = await fetch('/api/paste', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, filename }),
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || 'Processing failed');

            statusMessage.textContent = result.message;
            statusMessage.style.color = 'green';
            updateDocumentList();
        } catch (error) {
            statusMessage.textContent = 'Processing failed.';
            statusMessage.style.color = 'red';
            displayError(error.message);
        } finally {
            pasteInput.value = '';
        }
    });

    queryForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearAllOutputs();
        const query = queryInput.value;
        const selectedDoc = docSelect.value;

        if (!query) {
            displayError('Please enter a query.');
            return;
        }

        loader.style.display = 'block';
        statusMessage.textContent = '';

        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, selected_doc: selectedDoc }),
            });

            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || 'Query failed');

            // Render Answer
            answerEl.innerHTML = result.answer.replace(/\[(\d+)\]/g, ' <sup><a href="#source-$1" class="citation-link">[$1]</a></sup>');

            // Render Stats
            statsContainer.innerHTML = `
                <span>Time: ${result.duration}s</span> | 
                <span>Prompt Tokens: ${result.prompt_tokens}</span> | 
                <span>Completion Tokens: ${result.completion_tokens}</span> | 
                <span>Est. Cost: $${result.cost.toFixed(6)}</span>
            `;
            statsContainer.style.display = 'flex';

            // Render Sources
            if (result.sources.length > 0) {
                const sourcesHeader = document.createElement('h3');
                sourcesHeader.textContent = 'Cited Sources';
                sourcesContainer.appendChild(sourcesHeader);

                result.sources.forEach(source => {
                    const snippet = document.createElement('div');
                    snippet.className = 'source-snippet';
                    snippet.id = `source-${source.citation_num}`;

                    const header = document.createElement('div');
                    header.className = 'source-snippet-header';
                    header.textContent = `[${source.citation_num}] From: ${source.source_file}`;

                    const text = document.createElement('p');
                    text.className = 'source-snippet-text';
                    text.textContent = source.text;

                    snippet.appendChild(header);
                    snippet.appendChild(text);
                    sourcesContainer.appendChild(snippet);
                });
            }

        } catch (error) {
            displayError(error.message);
        } finally {
            loader.style.display = 'none';
        }
    });

    // Initial load
    updateDocumentList();
});