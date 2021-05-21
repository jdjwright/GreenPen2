fetch('http://localhost:8000/gquizalert', {
    method: 'POST',
    body: JSON.stringify({
        form_url: '',
        student_email: '',
        timestamp: ''
    }),
    headers: {
        'Content-type': 'application/json; charset=UTF-8'
    }
})
    .then(res => res.json())
    .then(console.log)