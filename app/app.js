const express = require('express');
const path = require('path');
const fileRoutes = require('./routes/fileRoutes');

const app = express();
const PORT = 3000;

// ✅ Serve static files (this must be before /api routes)
app.use(express.static(path.join(__dirname, 'public')));

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/api', fileRoutes);

// View route
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'views/index.html'));
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
