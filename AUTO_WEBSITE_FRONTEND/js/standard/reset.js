const $ = require('jquery');
const axios = require('axios');
import {event_func} from '../shared/shared_render_func';
const {global} = require('../../config.js');

function reset(reset_type, url) {
    // $('.reset_next_btn').on('click', () => {
    //     toggle_element_slide('next', reset_type);
    let user_field;
    let method = null;
    if (reset_type === 'email') {
        method = 'SMS';
    }
    if (reset_type === 'password') {
        $('#reset_select_method_submit').on('click', () => {
            method = $(`input[name='reset_select_method']`).filter(':checked').val();
            $('#reset_select_method_cont').slideUp();
        })
    }
    if (method !== null || undefined) {
        user_field = method;
        if (method === 'SMS') {
            user_field = 'mobile_no';
        }
    }
    const verify_cont = $(`#verify_${user_field}_method_cont`);
    verify_cont.slideDown();
    $(`#verify_${user_field}_method_submit`).on('click', () => {
        let user_field_data = $(`input[name='verify_${user_field}_method_input']`).val();
        if (user_field_data === null || typeof 'undefined') {
            const data = {
                method: method,
                reset_type: reset_type,
                [user_field]: user_field_data
            }
            axios.post(`${global.ngrok_api_url}${url}/reset/`, data, global.options)
            .then((res) => {
                verify_cont.slideUp();
                const code_cont = $('#reset_input_code_cont');
                code_cont.slideDown();
                $('#reset_input_code_submit').on('click', () => {
                    let user_input_otp = $(`input[name='reset_input_code']`).val();
                    const otp_data = {'user_input_otp': user_input_otp};
                    axios.post(`${global.ngrok_api_url}${url}/verify_otp/`, otp_data, global.options)
                    .then((res) => {
                        console.log(res.data.message);
                        code_cont.slideUp();
                        $(`reset_input_new_${reset_type}_cont`).slideDown();
                        $(`reset_input_new_${reset_type}_submit`).on('click', () => {
                            const input_new = $(`input[name='reset_new_${reset_type}_input']`).val();
                            const input_conf = $(`input[name='reset_conf_${reset_type}_input']`).val();
                            const input_data = {
                                [`new_${reset_type}`]: input_new,
                                [`confirm_${reset_type}`]: input_conf,
                            }
                            axios.post(`${global.ngrok_api_url}${url}/change/`, input_data, global.options)
                            .then((res) => {
                                console.log(res.data.message);
                            })
                            .catch((err) => {
                                console.log(err);
                            })
                        })
                    })
                    .catch((err) => {
                        console.log(err);
                    })
                })
            })
            .catch((err) => {
                console.log(err);
            })
        }
    })
}

export {reset}