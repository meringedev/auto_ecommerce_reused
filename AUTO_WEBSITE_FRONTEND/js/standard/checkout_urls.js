import {gen_func} from '../shared/shared_gen_func';

function checkout_url(window_obj, opts=null) {
    const url = gen_func.url_id_check(true);
    const is_id = url[0];
    const module_type = url[1];
    let suffix = module_type;
    let is_saved = false;
    let params = null;
    if (is_id) {
        id = url[2];
        suffix = suffix + `/${id}`;
        is_saved = true;
    } else {
        if (module_type === 'repair') {
            params = url[2];
            suffix = suffix + `/?${params}`;
        }
    }
    attrs = {
        'is_saved': is_saved,
        'module_type': module_type,
        'id': id,
        'suffix': suffix,
        'params': params
    }
    if (opts !== null) {
        return_attrs = opts.return_attrs;
        Object.keys(attrs).forEach(key => {
            if (!return_attrs.includes(key)) {
                delete attrs[key];
            }
        })
    }
    window_obj = attrs
}

export {checkout_url}