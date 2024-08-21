const axios = require('axios');
const $ = require('jquery');
import {gen_func} from '../shared/shared_gen_func';
const {check_user} = require('./sens');
const {global} = require('../../config.js');

let user_state = [false, false];