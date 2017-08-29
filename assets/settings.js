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

    function save(){
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
        promise.then(fetch_viewer).then(update_viewer);

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
        input.addEventListener('change', save);
    }

    // remove submit button since we're doing live updates
    let submit = form.querySelector('input[type=submit]');
    form.removeChild(submit);

    let status_display = document.createElement('span');
    status_display.classList.add('status-display', 'hidden');
    settings_section.insertBefore(status_display, settings_section.childNodes[0]);

    // silently send_settings in case the user changed settings while the page was loading
    send_settings(get_all_inputs());

    let viewer_update_interval = 1000;

    function fetch_viewer(){
        viewer_update_interval *= 2;
        viewer_update_interval = Math.min(30000, viewer_update_interval);
        return fetch('/api/viewer', {
            credentials: 'same-origin',
        })
            .then(resp => { if(!resp.ok){ return Promise.reject(resp) }; return resp; })
            .then(resp => resp.json());
    }

    let last_viewer = {}
    function update_viewer(viewer){
        if(JSON.stringify(last_viewer) == JSON.stringify(viewer)){
            return
        }

        document.querySelector('#post-count').textContent = viewer.post_count;
        document.querySelector('#eligible-estimate').textContent = viewer.eligible_for_delete_estimate;
        document.querySelector('#display-name').textContent = viewer.display_name || viewer.screen_name;
        document.querySelector('#display-name').title = '@' + viewer.display_name;
        document.querySelector('#avatar').src = viewer.avatar_url;
        viewer_update_interval = 1000;
        last_viewer = viewer;
    }

    function set_viewer_timeout(){
        setTimeout(() => fetch_viewer().then(update_viewer).then(set_viewer_timeout, set_viewer_timeout),
            viewer_update_interval);
    }
    set_viewer_timeout();
})();
