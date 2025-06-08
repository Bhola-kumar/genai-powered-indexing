const mammoth = require("mammoth");
const fs = require("fs");
const path = require("path");

exports.handleIndexUpload = async (req, res) => {
  const file = req.file;

  if (!file) {
    return res.status(400).json({ error: "No file uploaded." });
  }

  if (file.mimetype === 'application/pdf') {
    return res.json({ message: 'Index PDF uploaded successfully', file });
  }

  if (file.mimetype === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
    try {
      const result = await mammoth.convertToHtml({ path: file.path });
      return res.json({ message: "Index DOCX uploaded", file, html: result.value });
    } catch (err) {
      return res.status(500).json({ error: "Failed to parse DOCX" });
    }
  }

  return res.status(400).json({ error: "Unsupported file type." });
};

  
exports.handleChapterUpload = async (req, res) => {
  const file = req.file;
  if (!file) return res.status(400).json({ error: "No file uploaded." });

  if (file.mimetype === 'application/pdf') {
    return res.json({ message: 'Chapter PDF uploaded', file });
  }

  if (file.mimetype === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
    try {
      const result = await mammoth.convertToHtml({ path: file.path });
      return res.json({ message: "Chapter DOCX uploaded", file, html: result.value });
    } catch (err) {
      return res.status(500).json({ error: "Failed to parse DOCX" });
    }
  }

  return res.status(400).json({ error: "Unsupported file type." });
};
  
  // exports.handleUpdate = (req, res) => {
  //   // Simulate updated index output
  //   res.json({
  //     updatedContent: 'Updated index content based on uploaded files.'
  //   });
  // };
  