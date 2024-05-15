import React, {useEffect, useState} from 'react'
import {Routes, Route} from 'react-router-dom'
import axios from 'axios'
import { Link } from 'react-router-dom'
import Spinner from '../Components/Spinner'

const Home = () => {
  const [books, setBooks] = React.useState([])
  const [loading, setLoading] = React.useState(false)

  useEffect(()=> {
    setLoading(true)
    axios
        .get('http://localhost:5000/book')
            .then((response)=> {
                setLoading(false)
                setBooks(response.data.data)
            })
            .catch((error)=> {
                setLoading(false)
                console.log(error)
            })
  }, [])
  return (
    <div>
        <p className='font-bold text-[30px] text-center'>List of Books</p>
      {loading  ? (<Spinner />) : (
        <div>
            {books.map((book, index)=> (
                <>
                    <div className='flex flex-row space-x-[40px] bg-sky-500' key={book._id}>
                        <p>{index + 1}</p>
                        <p>{book.book_name}</p>
                        <p>{book.author}</p>
                        <p>{book.description}</p>
                        <img src={`http://localhost:5000/${book.image}`} className='w-[150px]' alt="Image" />
                        <Link to={`/delete/${book._id}`}>Delete</Link>
                        <Link to={`/update/${book._id}`}>Update</Link>
                    </div>

                   
                </>
            ))}
        </div>
      )}
       <Link to={'/add'} className='bg-slate-500 p-5 text-light flex justify-center mt-[10px]'>Add</Link>
    </div>
  )
}

export default Home
