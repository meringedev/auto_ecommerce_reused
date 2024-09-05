const axios = require('axios');
const $ = require('jquery');
import {gen_func} from '../shared/shared_gen_func';
const {check_user} = require('./sens');
const {global} = require('../../config.js');
const {conf_main_load} = require('./conf');

window.attrs = {};

attrs.is_saved = false;
attrs.module_type = null;
attrs.id = null;
attrs.params = null;
attrs.contains_ex = false;

let user_state = [false, false];

$(() => {
    user_state = check_user();
    gen_func.return_auth_page(user_state, {render_1: main_load});
})

function get_module_url() {
    let module_url;
    if (attrs.is_saved) {
        module_url = attrs.module_type + `/${attrs.id}`;
    } else {
        module_url = attrs.module_type;
    }
    return module_url
}

function main_load() {
    checkout_url(window.attrs);
    const axios_url = `${global.ngrok_api_url}/auth/checkout/${attrs.suffix}`;
    axios.get(axios_url, global.options)
    .then((res) => {
        const data = res.data;
        const checkout_total = data.checkout_total;
        const checkout_items = data.checkout_items;
        const user_addresses = data.user_addresses;
        const active_address = data.active_address.address_id;
        if (module_type === 'repair') {
            load_checkout_items(checkout_items, repair=true);
            const repair_saved = ['reason_repair', 'error_codes'];
            for (let repair_val of repair_saved) {
                const data_val = gen_func.get_prop(data, `saved_${repair_val}`);
                if (data_val !== null) {
                    $(`input[name='${repair_val}']`).val(data_val);
                }
            }
        }
        if (module_type === 'order') {
            load_checkout_items(checkout_items);
            load_exchange_units(data.checkout_contains_ex);
        }
        load_checkout_total(checkout_total);
        load_user_addresses(user_addresses, active_address);
    })
    .catch((err) => {
        console.log(err);
    })
}

function load_checkout_items(data, repair=false) {
    checkout_items_html_array = [];
    for (let item of data) {
        let img_location = `/public/${item.product_img_thumb}`;
        let inner_html;
        let data_attrs;
        if (repair) {
            inner_html = 
            `<div class="p-2">\n
                <h3 class="global_font_3 request_repair_item_name">MERCEDES-BENZ BASE MODULE</h3>\n
            </div>`
            data_attrs = `data-product-id="${item.product_id}"`
        }
        else {
            inner_html = 
            `<div class="p-2">\n
                <h3 class="global_font_3 checkout_items_for_delivery_product_name">${item.product_name}</h3>\n
                <p class="global_font_4 global_font_italic checkout_items_for_delivery_product_type">TYPE: ${item.variation_value}</p>\n
                <p class="global_font_4 global_font_italic checkout_items_for_delivery_product_qty">QTY: ${item.quantity}</p>\n
            </div>\n
            <div class="p-2">\n
                <h3 class="global_font_3 checkout_items_for_delivery_product_price">${item.total_price}</h3>\n
            </div>\n`
            data_attrs = `data-shopping-cart-item-id="${item.shopping_cart_item_id}" data-variation-id="${item.variation_id}" data-product-id="${item.product_id}"`
        }
        let html = `
        <div class="container checkout_items_for_delivery_indi_item_cont" ${data_attrs}>\n
            <div class="row">\n
                <div class="col-2">\n
                    <img src="${img_location}">\n
                </div>\n
                <div class="col">\n
                    <div class="d-flex flex-column">\n
                        ${inner_html}
                    </div>\n
                </div>\n
            </div>\n
        </div>
        `
        checkout_items_html_array.push(html);
    }
    $('.checkout_items_cont').append(checkout_items_html_array);
}

function load_user_addresses(data, active_address_id) {
    let user_addresses_html_array = [];
    const excluded = ['address_id', 'user_id', 'name', 'is_active', 'is_default']
    for (let item of data) {
        let address = [];
        let excluded_values = [];
        let is_active = False;
        for (let [key, value] of Object.entries(item)) {
            if (value !== null) {
                if (excluded.some(i => key.includes(i))) {
                    excluded_values.push(value);
                }
                else {
                    if (active_address_id === data.address_id) {
                        is_active = true;
                    }
                    address.push(`${value}<br>\n`);
                }
            }
        }
        let address_id = excluded_values[0];
        let name = excluded_values[2];
        address = address.toString();
        let inner_address_html = 
        `<p>${name}</p>\n
        <p>${address}</p>`;
        let address_html_class = 'container global_font_3 checkout_delivery_address_indi_item';
        if (is_active) {
            address_html_class = address_html_class + ' active';
            $('.checkout_delivery_address').data('shipping-address-id', address_id).text(inner_address_html);
        }
        let address_html =
        `<div class="${address_html_class}" data-shipping-address-id="${address_id}">\n
            ${inner_address_html}\n
        </div>`;
        user_addresses_html_array.push(address_html);
    }
    $('#checkout_delivery_address_scroll_cont').append(user_addresses_html_array);
}

function load_checkout_total(data) {
    let summary = [];
    let excluded = ['total_quantity', 'subtotal_excl', 'total'];
    let excluded_values = [];
    for (let [key, value] of Object.entries(data)) {
        if (value !== null || 0) {
            if (excluded.some(i => key.includes(i))) {
                excluded_values.push(value);
            }
            else {
                if (key.includes('vat')) {
                    head = `${key} (15%)`;
                }
                else {
                    head = key;
                }
                let html_row = 
                `<tr class="checkout_summary_table_row">\n
                    <td class="checkout_summary_table_head">${head}</td>\n
                    <td class="checkout_summary_table_data" id="checkout_summary_shipping">R${value}</td>\n
                </tr>\n`;
                summary.push(html_row);
            }
        }
    }
    let total;
    let extra_html;
    if (excluded_values.length === 3) {
        extra_html = 
        `<tr class="checkout_summary_table_row">\n
            <td class="checkout_summary_table_head">${excluded_values[0]} ITEMS</td>\n
            <td class="checkout_summary_table_data" id="checkout_summary_shipping">R${excluded_values[1]}</td>\n
        </tr>\n`;
        total = excluded_values[2];
    }
    else {
        extra_html = '';
        total = excluded_values[0];
    }
    summary = summary.toString();
    let html = 
    `${extra_html}${summary}
    <tr class="checkout_summary_table_row">\n
        <td class="checkout_summary_table_blank"></td>\n
        <td class="checkout_summary_table_blank"></td>\n
    </tr>\n
    <tr class="checkout_summary_table_row">\n
        <td class="checkout_summary_table_head">TOTAL:</td>\n
        <td class="checkout_summary_table_data checkout_summary_table_total_data" id="checkout_summary_total">R${total}</td>\n
    </tr>`;
    $('table.checkout_summary_table > tbody').append(html);
}

function load_exchange_units(data) {
    if (data === true) {
        $('.checkout_exchange_unit_cont').show();
        window.attrs.contains_ex = true;
        if (window.attrs.is_saved === true) {
            const saved_files = gen_func.get_prop(data, 'saved_ex_unit_files');
            for (let saved_file of saved_files) {
                let user_filename = saved_file.user_filename;
                let internal_filename = saved_file.order_ex_unit_filename
                let html = `<p class="checkout_exchange_unit_photo_file_name global_font_italic" data-user-filename="${user_filename}" data-file-status="current" data-internal-filename="${internal_filename}">${user_filename}<button type="button" class="btn global_remove_shadow global_black_icon_btn checkout_exchange_unit_photo_file_remove"><i class="fa-solid fa-trash fa-sm"></i></button></p>`;
                $(html).appendTo('.checkout_exchange_unit_photo_file_cont');
                attrs.files_current.push(internal_filename);
            }
        }
    }
}

function get_shipping_method(method_id, address_id=null) {
    data = {
        'shipping_method_id': method_id,
    }
    if (address_id !== null) {
        data.append('shipping_address_id', address_id)
    }
    const axios_url = `${global.ngrok_api_url}/auth/checkout/get_shipping_method/`;
    axios.post(axios_url, data, global.options)
    .then((res) => {
        load_checkout_total(res.data);
    })
    .catch((err) => {
        console.log(err);
    })
}

if (attrs.contains_ex === true) {
    attrs.files_to_upload = [];
    // attrs.files_to_delete = [];
    attrs.files_current = [];
}

$('checkout_exchange_unit_upload').on('change', () => {
    const filelist = $(this).prop('files');
    for (let file of filelist) {
        attrs.files_to_upload.push(file);
        let html = `<p class="checkout_exchange_unit_photo_file_name global_font_italic" data-user-filename="${file.name}" data-file-status="new">${file.name}<button type="button" class="btn global_remove_shadow global_black_icon_btn checkout_exchange_unit_photo_file_remove"><i class="fa-solid fa-trash fa-sm"></i></button></p>`;
        $(html).appendTo('.checkout_exchange_unit_photo_file_cont');
    }
})

$('.checkout_exchange_unit_photo_file_remove').on('click', () => {
    const popup = '#checkout_exchange_unit_file_delete';
    const btn = '#checkout_change_delivery_address_cont';
    $(popup).modal('show');
    const current_file = $(this).parent();
    const user_filename = current_file.data('user-filename');
    const file_status = current_file.data('file-status');
    $(`${btn}_submit`).on('click', () => {
        if (file_status === 'current') {
            const internal_filename = current_file.data('internal-filename')
            const axios_url = `${global.ngrok_api_url}/upload?filename=${internal_filename}`;
            axios.delete(axios_url, global.options)
            .then((res) => {
                current_file.remove();
            })
            .catch((err) => {
                console.log(err);
            })
        }
        if (file_status === 'new') {
            for (let file of attrs.files_to_upload) {
                if (file.name === user_filename) {
                    attrs.files_to_upload.pop(file);
                }
            }
            current_file.remove();
        }
    })
})

$('.checkout_delivery_method_btns').on('click', () => {
    let containers = ['checkout_delivery_address', 'checkout_pickup_address', 'checkout_courier_notice_cont']
    $('.checkout_delivery_method_btns').not(this).removeClass('active');
    $(this).addClass('active');
    let shipping_method_id = $(this).data('shipping_method_id');
    let shipping_address_id;
    let conts;
    if (shipping_method_id === 1) {
        conts = [containers[0]];
    }
    else {
        if (shipping_method_id === 2) {
            conts = [containers[1], containers[2]];
        }
        if (shipping_method_id === 3 || 4) {
            conts = [containers[3]];
        }
        shipping_address_id = null;
    }
    let cont = conts.join(', ');
    $(cont).show();
    for (let element of containers) {
        if ($(element).is(':visible')) {
            for (let item of conts) {
                if (element !== item) {
                    $(element).hide();
                }
            }
        }
    }
    get_shipping_method(shipping_method_id, shipping_address_id);
})

$('#checkout_delivery_address_change_popup').on('click', () => {
    const popup = '.checkout_delivery_address_change_popup'
    const item = '.checkout_delivery_address_indi_item'
    $(popup).modal('show');
    $(item).on('click', () => {
        $(item).not(this).removeClass('active');
        $(this).addClass('active');
    })
    $('#checkout_change_delivery_address_cont_submit').on('click', () => {
        let active_item = $(item).find('active');
        let shipping_address_id = $(active_item).data('shipping-address-id');
        let address = $(active_item).clone().find('div').remove();
        $('.checkout_delivery_address').text(address).data('shipping-address-id', shipping_address_id).trigger('get_shipping_method', [1, shipping_address_id]);
    })
    $('#checkout_change_delivery_address_cont_close').on('click', () => {
        $(popup).modal('show');
    })
})

function get_extra_vals() {
    let data = {};
    if (attrs.module_type === 'order') {
        if (attrs.contains_ex) {
            if (length(attrs.files_to_upload) !== 0) {
                let url = `${global.ngrok_api_url}/upload/?user_type=user&instance_type=${attrs.module_type}`;
                if (attrs.is_saved) {
                    url = url + `&instance_id=${attrs.id}`;
                }
                let data = new FormData();
                for (let file of attrs.files_to_upload) {
                    data.append('file', file);
                }
                axios.post(url, data, global.options)
                .then((res) => {
                    res.data.filenames.forEach((filename) => {
                        attrs.files_current.push(filename);
                    })
                })
            }
            data.append('ex_unit_images', attrs.files_current);
        }
    }
    if (attrs.module_type === 'repair') {
        const inputs = ['#checkout_repair_reason_input', '#checkout_repair_error_code_input'];
        for (const input of inputs) {
            const val = $(input).val();
            const input_name =  $(input).data('input-name');
            if (val === typeof 'undefined' || 'null') {
                data.append(input_name, val);
            }
        }
    }
    return data
}

function get_main_vals(extra_data=null) {
    $('.checkout_payment_message').text('...redirecting');
    let data = {};
    if (extra_data !== null) {
        data = {
            ...extra_data
        }
    }
    const shipping_method_id = $('.checkout_delivery_method_btns').find('active').data('shipping_method_id');
    data.append('shipping_method_id', shipping_method_id);
    if (shipping_method_id === 1) {
        const shipping_address_id = $('.checkout_delivery_address').data('shipping-address-id');
        data.append('shipping_address_id', shipping_address_id);
    }

    const module_url = get_module_url();

    return [data, module_url]
}

function get_data() {
    let data = get_extra_vals();
    [data, module_url] = get_main_vals(data);

    return [data, module_url]
}

$('#checkout_pre_transaction_btn').on('click', () => {
    [data, module_url] = get_data(data);

    let axios_url = `${global.ngrok_api_url}/auth/checkout/${module_url}/init/pre_transaction`;
    if (attrs.params !== null) {
        axios_url += `?${params}`;
    }
    axios.post(axios_url, data, global.options)
    .then((res) => {
        payment_load(res.data);
    })
})

$('#checkout_save').on('click', () => {
    [data, module_url] = get_data(data);

    let axios_url = `${global.ngrok_api_url}/auth/checkout/${module_url}/save`;
    if (attrs.params !== null) {
        axios_url += `?${params}`;
    }
    axios.post(axios_url, data, global.options)
    .then((res) => {
        if (res.data.message === 'saved!') {
            window.location.replace('/shopping-cart');
        }
    })
    .catch((err) => {
        console.log(err);
    })
})

function payment_load(data) {
    load_bank_accounts(data);
    load_checkout_total(data);
}

function load_bank_accounts(data) {
    bank_accounts = gen_func.get_prop(data, 'user_bank_accounts');
    const main_cont = '#checkout_payment_bank_account_cont';
    if (bank_accounts !== null) {
        const excluded = ['user_id', 'gc_customer_id', 'gc_customer_bank_account_id'];
        for (const account of bank_accounts) {
            let render = [];
            const html = $('.checkout_payment_bank_account_indi_item').clone();
            for (const [key, value] of Object.entries(account)) {
                if (value !== null) {
                    if (!excluded.some(i => key.includes(i))) {
                        render.push(`${value}<br>\n`);
                    }
                }
            }
            html.data('gc-customer-id', account.gc_customer_id);
            html.data('gc-customer-bank-account-id', account.gc_customer_bank_account_id);
            render = render.toString();
            html.text(`<p>${render}</p>`);
            html.show();
            html.appendTo(main_cont);
        }
    } else {
        const message = '<p>No bank accounts to show here!<br>Create a new one!</p>';
        $(message).appendTo(main_cont);
    }
}

$('#checkout_payment_bank_account_change').on('click', () => {
    const popup_cont = '#checkout_payment_change_popup'
    $(popup_cont).modal('show');
    $('#checkout_payment_change_bank_account_cont_close').on('click', () => {
        $('#checkout_payment_change_popup').modal('hide');
    })
    let gc_customer_id = null;
    let gc_customer_bank_account_id = null;
    $('.checkout_payment_bank_account_indi_item').on('click', () => {
        $('.checkout_payment_bank_account_indi_item').removeClass('active');
        $(this).addClass('active');
        gc_customer_id = $(this).data('gc-customer-id');
        gc_customer_bank_account_id = $(this).data('gc-customer-bank-account-id');
    })
    $('#checkout_payment_change_bank_account_cont_submit').on('click', () => {
        attrs.bank_account_data = {
            'gc_customer_id': gc_customer_id,
            'gc_customer_bank_account_id': gc_customer_bank_account_id
        }
        $(popup_cont).modal('hide');
    })
    $('#checkout_payment_change_bank_account_cont_create_new').on('click', () => {
        let has_errors = false;
        const billing_details_cont = '#checkout_payment_create_new_bd_cont';
        const account_details_cont = '#checkout_payment_create_new_ad_cont';
        const review_details_cont = '#checkout_payment_create_new_ra_cont';
        const message_cont = '.checkout_payment_create_new_bd_message';
        const error_message = 'Mandatory fields not filled';
        $(popup_cont).slideUp();
        $(billing_details_cont).slideDown();
        let billing_address_data = {};
        let bank_account_data = {};
        $('.checkout_payment_change_bank_account_cont_close').on('click', () => {
            $(popup_cont).modal('hide');
            billing_address_data = {};
            bank_account_data = {};
            $(`input:text`).val('');
        })
        $('#checkout_payment_create_new_bd_next').on('click', () => {
            $('.checkout_payment_create_new_bd_input').each(() => {
                const key = $(this).attr('name');
                const val = $(this).val();
                if (val !== '') {
                    billing_address_data.append(key, val);
                } else {
                    has_errors = true;
                }
            })
            if (has_errors !== true) {
                $(billing_details_cont).slideUp();
                $(account_details_cont).slideDown();
                $(message_cont).text('');
            } else {
                billing_address_data = {};
                $(message_cont).text(error_message);
            }
            if ($('#checkout_payment_create_ad_use_iban_check').is(':checked')) {
                $('#checkout_payment_create_new_ad_iban_cont').show();
                let is_iban = true;
            } else {
                is_iban = false;
            }
            $('#checkout_payment_create_new_ad_next').on('click', () => {
                const excluded_ad = ['gc_account_number'];
                $('.checkout_payment_create_new_bd_input').each(() => {
                    const key = $(this).attr('name');
                    const val = $(this).val();
                    if (!excluded_ad.some(i => key.includes(i))) {
                        if (is_iban === false) {
                            if (val === '') {
                                has_errors = true;
                            }
                        }
                    }
                    bank_account_data.append(key, val);
                })
                if (is_iban) {
                    const iban_key = 'gc_iban';
                    const iban_val = $(`input[name='${iban_key}']`).val();
                    if (iban_val === '') {
                        has_errors = true;
                    }
                }
                if (has_errors !== true) {
                    $(message_cont).text('');
                    $(account_details_cont).slideUp();
                    $(review_details_cont).slideDown();
                    const combined_data = {
                        ...billing_address_data,
                        ...bank_account_data
                    };
                    for (const [key, value] of Object.entries(combined_data)) {
                        review_details_cont.find(`[data-insert-item-value='${key}']`).text(value);
                    }
                } else {
                    bank_account_data = {};
                    $(message_cont).text(error_message);
                }
            })
            $('#checkout_payment_change_new_ba_submit').on('click', () => {
                attrs.bank_account_data = {
                    'create_new_account': true,
                    'gc_billing_details': billing_address_data,
                    'gc_bank_account_data': bank_account_data
                }
                $(popup_cont).modal('hide');
            })
        })
    })
})

function post_transaction() {
    const data = attrs.bank_account_data;

    const module_url = get_module_url();

    const axios_url = `${global.ngrok_api_url}/auth/checkout/${module_url}/init/post_transaction`;
    window.location.replace('/checkout/load');
    axios.post(axios_url, data, global.options)
    .then((res) => {
        window.location.replace(`/checkout/conf/${attrs.module_type}`);
        conf_load(res.data);
    })
    .catch((err) => {
        console.log(err);
        const data = err.res.data;
        const flag = data.flag;
        if (flag === 'cancelled') {
            window.location.replace('/checkout/cancelled');
            $('#checkout_payment_cancel_message').text(data.message);
        }
    })
}

$('#checkout_post_transaction_btn').on('click', () => {
    post_transaction();
})

function output_message(data) {
    $('#checkout_cancel_message').text(data.message);
    $('#checkout_cancel_btn').remove();
}

$('#checkout_cancel_btn').on('click', () => {
    const module_url = get_module_url();
    const axios_url = `${global.ngrok_api_url}/auth/checkout/${module_url}/cancel_transaction`;
    axios.post(axios_url, global.options)
    .then((res) => {
        output_message(res.data);
    })
    .catch((err) => {
        console.log(err);
        output_message(err.res.data);
    })
})

function conf_load(data) {
    conf_main_load(data, {module_type: attrs.module_type});
}