import React, {useState, useEffect} from 'react'
import axios from 'axios'
import Spinner from '../Components/Spinner'
import { useNavigate, useParams } from 'react-router-dom'

const UpdateBook = () => {
  const [book_name, setBookName] = React.useState('')
  const [author, setAuthor] = React.useState('')
  const [description, setDescription] = React.useState('')
  const [loading, setLoading] = React.useState(false)
  const navigate = useNavigate()
  //destructuring the id from the backend
  const { id } = useParams()

  //then update
  useEffect(()=> {
      setLoading(true)
      axios.get(`http://localhost:5000/book/${id}`)
        .then((response)=> {
            setBookName(response.data.book_name)
            setAuthor(response.data.author)
            setDescription(response.data.description)
            setLoading(false)
        })
        .catch((error)=> {
          console.log(error)
          setLoading(false)
        })
  }, [])

  //function to handle save book
  const handleEditBook = ()=> {
    const data = {
      book_name,
      author,
      description
    }

    //then hanle saving book
    setLoading(true)
    //use axios to send request to backend
    axios
      .put(`http://localhost:5000/book/update/${id}`, data)
        .then(()=> {
            setLoading(false)
            navigate('/')
        })
        .catch((error)=> {
            setLoading(false)
            console.log(error)
        })
  }

  return (
    <div className='p-[50px]'>
      
      <div className="mb-[10px]">
        <input className="border-2 border-slate-500 pl-[15px] w-[300px] pt-[10px] pb-[10px] focus:border-green-500 outline-0" type="text" value={book_name} onChange={(e)=> setBookName(e.target.value)} placeholder="Book name" />
      </div>
      <div className="mb-[10px]">
        <input className="border-2 border-slate-500 pl-[15px] w-[300px] pt-[10px] pb-[10px] focus:border-green-500 outline-0" type="text" value={author} onChange={(e)=> setAuthor(e.target.value)} placeholder="Author" />
      </div>
      <div className="mb-[10px]">
        <input className="border-2 border-slate-500 pl-[15px] w-[300px] pt-[10px] pb-[10px] focus:border-green-500 outline-0" type="text" value={description} onChange={(e)=> setDescription(e.target.value)} placeholder="Description" />
      </div>
      <div>
        <div>
            {loading ? <Spinner /> : ''}
        </div>
        <button className='bg-green-500 text-white pl-[30px] pr-[30px] pt-[15px] pb-[15px] rounded-[10px]' onClick={handleEditBook}>Edit</button>
      </div>
    </div>
  )
}

export default UpdateBook
