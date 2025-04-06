Initialize Node.js Project (if not already done):
```
npm init -y
```

Install Dependencies:
```
npm install express cors multer
```

Run the Server:
```
node server.js
```


```
curl -X POST "http://localhost:8000/chat/agentstream" \
-H "Content-Type: application/json" \
-d '{"message": "法国首都在哪里", "model": "gpt-3.5-turbo", "temperature": 0.7}'
```