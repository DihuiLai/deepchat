const express = require('express');
const cors = require('cors');
const multer = require('multer');
const fs = require('fs');
const path = require('path');
const marked = require('marked');
const app = express();
const port = 3000;

// Middleware
app.use(cors());
app.use(express.static(__dirname));
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
// Ensure uploads directory exists
const uploadDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir);
}

// Configure multer for file uploads
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, 'uploads/');
    },
    filename: (req, file, cb) => {
        cb(null, Date.now() + '-' + file.originalname);
    }
});
const upload = multer({ storage: storage });

// Dummy responses
const dummyResponses = [
    // Existing responses...
    "Hey there! Here's a quick reply: **bold** text works! How can I assist you today?",
    "Interesting question! Here's some code for you:\n```\nfunction sayHi() {\n  console.log('Hi!');\n}\n```\nWhat else can I do?",
    "I'm Grok, built by xAI. Let me think... How about this: `inline code` is neat, right?",
    JSON.stringify({
        status: "success",
        message: "Hello from Grok!",
        data: { id: 42, name: "Test" }
    }),
    // New table response
    `Here's a table for you: \n` +
                    `| Name    | Age | City       |\n` +
                    `|---------|-----|------------|\n` +
                    `| John    | 25  | New York   |\n` +
                    `| Alice   | 30  | London     |\n` +
                    `| Bob     | 35  | Sydney     |`
];

// Serve the index.html file at the root
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// POST endpoint for chat and file upload with streaming
app.post('/grok', upload.single('file'), (req, res) => {
    console.log('Request received:', req.body, req.file);

    const message = req.body ? req.body.message : undefined;
    const file = req.file;

    // Set headers for streaming
    res.setHeader('Content-Type', 'text/plain');
    res.setHeader('Transfer-Encoding', 'chunked');

    let response = dummyResponses[Math.floor(Math.random() * dummyResponses.length)];
    if (file) {
        response = `Received file: **${file.originalname}** (Type: ${file.mimetype}, Size: ${file.size} bytes)`;
    } else if (!message) {
        response = "Please send a message or upload a file!";
    }

    // Stream the response character by character
    let index = 0;
    const streamInterval = setInterval(() => {
        if (index < response.length) {
            res.write(response[index]);
            index++;
        } else {
            clearInterval(streamInterval);
            res.end(); // End the stream
        }
    }, 5); // 50ms delay per character
});

app.post('/convert-markdown', (req, res) => {
    const { text } = req.body;
    if (!text) {
        return res.status(400).json({ error: 'No text provided' });
    }

    let html;
    let isJson = false;
    let hasCodeOrTable = false;
    try {
        const jsonData = JSON.parse(text);
        html = `<pre style="background: #f0f0f0; padding: 10px; border-radius: 5px;">${JSON.stringify(jsonData, null, 2)}</pre>`;
        isJson = true;
        hasCodeOrTable = true; // JSON counts as code
    } catch (e) {
        html = marked.parse(text);
        // Check for code blocks or tables in markdown
        hasCodeOrTable = text.includes('```') || text.includes('|');
    }

    res.json({ html, raw: text, isJson, hasCodeOrTable });
});

// Start server
app.listen(port, () => {
    console.log(`DeepChat server running at http://localhost:${port}`);
});