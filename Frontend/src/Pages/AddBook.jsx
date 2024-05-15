import React, {useState} from 'react'
import axios from 'axios'
import Spinner from '../Components/Spinner'
import { useNavigate } from 'react-router-dom'

const AddBook = () => {
  const [book_name, setBookName] = useState('')
  const [author, setAuthor] = useState('')
  const [description, setDescription] = useState('')
  const [image, setImage] = useState(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleImageChange = (e) => {
    setImage(e.target.files[0]);  // Correctly capture the first file
  };
  
  //function to handle save book
  const handleSaveBook = (e)=> {
    e.preventDefault();

    const data = {
      book_name,
      author,
      description,
      image
    }

    //then hanle saving book
    setLoading(true)
    //use axios to send request to backend
    axios
      .post('http://localhost:5000/book/add', data, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
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
      <form encType="multipart/form-data">
          <div className="mb-[10px]">
            <input className="border-2 border-slate-500 pl-[15px] w-[300px] pt-[10px] pb-[10px] focus:border-green-500 outline-0" type="text" value={book_name} onChange={(e)=> setBookName(e.target.value)} placeholder="Book name" />
          </div>
          <div className="mb-[10px]">
            <input className="border-2 border-slate-500 pl-[15px] w-[300px] pt-[10px] pb-[10px] focus:border-green-500 outline-0" type="text" value={author} onChange={(e)=> setAuthor(e.target.value)} placeholder="Author" />
          </div>
          <div className="mb-[10px]">
            <input className="border-2 border-slate-500 pl-[15px] w-[300px] pt-[10px] pb-[10px] focus:border-green-500 outline-0" type="text" value={description} onChange={(e)=> setDescription(e.target.value)} placeholder="Description" />
          </div>
          <div className="mb-[10px]">
            <input className="border-2 border-slate-500 pl-[15px] w-[300px] pt-[10px] pb-[10px] focus:border-green-500 outline-0" type="file" name='image' onChange={handleImageChange} />
          </div>
          <div>
            <div>
                {loading ? <Spinner /> : ''}
            </div>
            <button className='bg-green-500 text-white pl-[30px] pr-[30px] pt-[15px] pb-[15px] rounded-[10px]' onClick={handleSaveBook}>Save</button>
          </div>

      </form>
    </div>
  )
}

export default AddBook
