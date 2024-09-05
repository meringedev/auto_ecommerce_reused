const axios = require('axios');
const $ = require('jquery');
import {gen_func} from '../shared/shared_gen_func';
const {check_user} = require('./sens');
const {global} = require('../../config.js');
const {checkout_url} = require('./checkout_urls');

window.attrs = {};

attrs.is_saved = false;
attrs.module_type = null;
attrs.id = null;
attrs.params = null;

let user_state = [false, false];

$(() => {
    user_state = check_user();
    gen_func.render_auth_page(user_state, {render_1: main_load});
})

function main_load() {
    checkout_url(window.attrs);
    
}