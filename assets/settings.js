(function(){
    if(!('fetch' in window)){
        return;
    }

    let status_timeout = null;

    let settings_section = document.querySelector('#settings-section');
    let form = document.forms.settings;
    let backoff_level = 0

    function hide_status(){
        status_display.classList.remove('error', 'success', 'saving');
        status_display.classList.add('hidden');
        status_display.innerHTML='';
    }
    function show_error(e){
        hide_status();
        status_display.textContent='Could not save. Retrying...';
        status_display.classList.add('error');
        status_display.classList.remove('hidden');
    }
    function show_success(){
        hide_status();
        status_display.textContent='Saved!';
        status_display.classList.add('success');
        status_display.classList.remove('hidden');
    }
    function show_saving(){
        hide_status();
        status_display.textContent='Saving...';
        status_display.classList.add('saving');
        status_display.classList.remove('hidden');
        status_timeout = setTimeout(show_still_saving, 5000);
    }
    function show_still_saving(){
        status_display.textContent='Still saving...';
    }

    function on_change(e){
        hide_status();
        clearTimeout(status_timeout);
        status_timeout = setTimeout(show_saving, 70);

        promise = send_settings(get_all_inputs())
            .then(data => {
                show_success();
                clearTimeout(status_timeout);
                status_timeout = setTimeout(hide_status, 3000);
                backoff_level = 0;
            });
        promise.catch(e => {
                console.error('Fetch rejected:', e);
                show_error();
                clearTimeout(status_timeout);
                status_timeout = setTimeout(save, Math.pow(2, backoff_level)*1000);
                backoff_level += 1;
                backoff_level = Math.min(backoff_level, 5);
            });
        promise.then(fetch_counters).then(update_counters);

        // remove server-rendered banner
        let banner = settings_section.querySelector('.banner');
        if(banner){
            settings_section.removeChild(banner);
        }
    }

    function get_all_inputs(){
        let o = Object()
        for(input of form.elements){
            if(input.type != 'radio' || input.checked){
                o[input.name] = input.value;
            }
        }
        return o
    }

    function send_settings(body){
        return fetch('/api/settings', {
            method:'PUT',
            credentials:'same-origin',
            headers: {
                'content-type': 'application/json',
            },
            body: JSON.stringify(body)
        })
            .then(resp => { if(!resp.ok){ return Promise.reject(resp) }; return resp; })
            .then(resp => resp.json())
            .then(data => {
                if(data.status == 'error'){ return Promise.reject(data) }
                return data
            });
    }

    for(input of form.elements){
        input.addEventListener('change', on_change);
        input.addEventListener('change', e=>console.log(e.target));
    }

    // remove submit button since we're doing live updates
    let submit = form.querySelector('input[type=submit]');
    form.removeChild(submit);

    let status_display = document.createElement('span');
    status_display.classList.add('status-display', 'hidden');
    settings_section.insertBefore(status_display, settings_section.childNodes[0]);

    // silently send_settings in case the user changed settings while the page was loading
    send_settings(get_all_inputs());

    function fetch_counters(){
        return fetch('/api/viewer', {
            credentials: 'same-origin',
        })
            .then(resp => { if(!resp.ok){ return Promise.reject(resp) }; return resp; })
            .then(resp => resp.json());
    }

    function update_counters(counters){
        document.querySelector('#post-count').textContent = counters.post_count;
        document.querySelector('#eligible-estimate').textContent = counters.eligible_for_delete_estimate;
    }

    setInterval(() => fetch_counters().then(update_counters), 1000 * 20)
})();
