const express = require('express');
const multer = require('multer');
const { handleIndexUpload, handleChapterUpload, handleUpdate } = require('../controllers/fileController');

const router = express.Router();

const storage = multer.diskStorage({
  destination: 'public/uploads/',
  filename: (req, file, cb) => {
    const safeName = file.originalname.replace(/\s+/g, '_');
    cb(null, `${Date.now()}-${safeName}`);
  }
});

const upload = multer({ storage });

router.post('/upload-index', upload.single('file'), handleIndexUpload);
router.post('/upload-chapter', upload.single('file'), handleChapterUpload);
// router.post('/update-index', handleUpdate);

module.exports = router;
