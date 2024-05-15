const path = require('path')
const multer = require('multer')

//logic for uploading
let storage = multer.diskStorage({
    destination: function(req, file, cb) {
        cb(null, 'uploads')
    },
    filename: function(req, file, cb) {
        let ext = path.extname(file.originalname)
        cb(null, Date.now() + ext)
    }
})

//file verification
let upload = multer({
    storage: storage,
    //filter the files
    fileFilter: function(req, file, callback) {
        if(file.mimetype == "image/png" || file.mimetype == "image/jpg") {
            callback(null, true)
        }else{
            console.log('Only image of png and jpg are allowed')
        }
    },
    //limit file sizes
    limits: {
        fileSize: 1024 * 1024 * 2
    }
})

module.exports = upload