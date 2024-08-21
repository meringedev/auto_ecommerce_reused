const express = require('express');
const path = require('path');
const axios = require('axios');
const cors = require('cors');
const fs = require('fs');
const jsdom = require('jsdom');
const {global} = require('./js/shared/CJS/config.js');
const {email_render} = require('./email_render.js');
const {invoice_func} = require('./invoice_render.js');

const whitelist = ['http://localhost:3000', 'http://host.docker.internal:3000', global.ngrok_api_url];

const allowed_headers = ['Content-Type', 'Accept', 'Authorization', 'ngrok-skip-browser-warning', 'Set-Cookie'];

const cors_options = {
    origin: whitelist,
    optionsSuccessStatus: 200,
    allowedHeaders: allowed_headers,
    credentials: true
}

const global_cors = cors(cors_options)

const app = express();

app.use(global_cors);
app.use(express.json());

app.post('render/:type', (req, res) => {
    const needs_render = req.body.needs_render;
    if (needs_render === true) {
        try {
            const params = req.params.type;
            const data = req.body;
            if (params === 'email') {
                const html_type = data.html_template_type;
                let content;
                switch (html_type) {
                    case 'OTP':
                        content = email_render.new_otp_email(data);
                        break;
                    case 'conf':
                        content = email_render.new_status_email(data);
                        break;
                    case 'status':
                        content = email_render.new_conf_email(data);
                    default:
                        res.json({message: 'not a valid html type!'});
                }
                // const _retfile = file_attr[0];
                // const file_path = file_attr[1];
                // console.log(_retfile);
                // console.log(file_path);
                // const start = _retfile.indexOf('/opt/node_app/media');
                // const end = start + '/opt/node_app/media'.length;
                // const _retfile_sliced = _retfile.slice(0, start) + _retfile.slice(end);
                // console.log(_retfile_sliced)
                // const bootstrap_email = new BootstrapEmail(_retfile);
                // const compiled_email = bootstrap_email.compile();
                // fs.writeFileSync(file_path, compiled_email, (err) => {
                //     if (err) {
                //         console.log(err);
                //     } else {
                //         console.log('success!');
                //     }
                // })
                console.log('compiled');
                res.json({message: 'successful', content: content});
            }
            if (params === 'invoice') {
                invoice_func.invoice_render(data);
            }
        } catch (err) {
            console.log(err);
        }
    }
})

app.listen(8070, () => {
    console.log('Listening on port ' + 8070)
})