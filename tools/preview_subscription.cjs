// Local production-export QA. No requests are forwarded to the live API.
const express = require('express');
const path = require('node:path');
const app = express();
app.post(['/api/lead', '/api/event'], express.raw({type:'application/json',limit:'24kb'}), async (req,res) => {
 try {
  const response = await fetch('http://127.0.0.1:8790'+req.path,{method:'POST',headers:{'Content-Type':'application/json'},body:req.body,signal:AbortSignal.timeout(35000)});
  res.status(response.status).type('application/json').send(await response.text());
 } catch { res.status(503).json({ok:false}); }
});
app.use(express.static(path.join(__dirname,'../dist'),{extensions:['html']}));
app.listen(4600,'127.0.0.1',()=>console.log('Local export preview: http://127.0.0.1:4600'));
