const Book = require('../Models/Book')


//add book
const store = function(req,res) {
    let book = new Book({
        book_name: req.body.book_name,
        author: req.body.author,
        description: req.body.description
    })
    //upload file
    if(req.file) {
        book.image = req.file.path
    }

    //add book
    book.save()
        .then(()=> {
            res.json({
                message: 'Book added'
            })
        })
        .catch(()=> {
            console.log('Error')
            res.json({
                message: 'Failed to add the book'
            })
        })
}



//update book
const update = function(req,res) {
    //find the bookid
    const { id } = req.params

    let updatedBook = {
        book_name: req.body.book_name,
        author: req.body.author,
        description: req.body.description
    }

    //update book
    Book.findByIdAndUpdate(id, {$set: updatedBook})
        .then(() => {
            res.json({
                message: 'Book updated'
            })
        })
        .catch((error) => {
            console.log(error)
            res.json({
                message: 'Failed to update the book'
            })
        })
}

//find one book
const show = function(req,res) {
    const { id } = req.params
    Book.findById(id)
        .then((response)=> {
            res.json({
                response
            })
            
        })
        .catch((error)=> {
            console.log(error)
            res.json({
                message: "Failed to fetch the user"
            })
        })
}

//delete book
const destroy = function(req, res) {
    const { id } = req.params
    Book.findByIdAndDelete(id) 
        .then(()=> {
            res.json({
                message: 'Book Deleted'
            })
        })
        .catch((error)=> {
            console.log(error)
            res.json({
                message: 'Failed to delete book'
            })

            
        })
}

//show all books
const index = function(req, res) {
    Book.find()
        .then((data)=> {
            res.json({
                data
            })
        })
        .catch((error)=> {
            console.log(error)
            res.json({
                message: 'Failed to fetch books'
            })
        })

}

//find sinlge book
const single = function(req,res) {
    const { id } = req.params
    Book.findById(id)
        .then((data)=> {
            res.json({
                data
            })
        })
        .catch((error) => {
            console.log(error)
            res.json({
                message: 'Failed to fetch book'
            })
        }) 
}
 



module.exports = {store, update, show, destroy, index, single}