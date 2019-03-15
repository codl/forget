import Banner from '../components/Banner.html';
import ArchiveForm from '../components/ArchiveForm.html';
import {known_load, known_save} from './known_instances.js'

(function settings_init(){
    if(!('fetch' in window)){
        return;
    }

    let status_timeout = null;

    let settings_section = document.querySelector('#settings-section');
    let form = document.querySelector('form[name=settings]');
    let inputs = Array.from(form.elements)
    let backoff_level = 0;

    let banner_el = document.querySelector('.main-banner');
    banner_el.innerHTML = '';
    let banner = new Banner({
        target: banner_el,
    });

    function hide_status(){
        status_display.classList.remove('error', 'success', 'saving');
        status_display.classList.add('hidden');
        status_display.innerHTML='';
    }
    function show_error(){
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
    function show_still_saving(){
        status_display.textContent='Still saving...';
    }
    function show_saving(){
        hide_status();
        status_display.textContent='Saving...';
        status_display.classList.add('saving');
        status_display.classList.remove('hidden');
        status_timeout = setTimeout(show_still_saving, 5000);
    }

    function save(){
        hide_status();
        clearTimeout(status_timeout);
        status_timeout = setTimeout(show_saving, 70);

        let promise = send_settings(get_all_inputs())
            .then(() => {
                show_success();
                clearTimeout(status_timeout);
                status_timeout = setTimeout(hide_status, 3000);
                backoff_level = 0;
            });
        promise.catch(() => {
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
        let o = Object();
        for(let input of inputs){
            if(input.type != 'radio' || input.checked){
                o[input.name] = input.value;
            }
        }
        return o;
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
            .then(resp => {
                if(!resp.ok){ return Promise.reject(resp); }
                return resp; })
            .then(resp => resp.json())
            .then(data => {
                if(data.status == 'error'){ return Promise.reject(data); }
                return data;
            });
    }

    for(let input of inputs){
        input.addEventListener('change', save);
    }

    // remove submit button since we're doing live updates
    let submit = form.querySelector('input[type=submit]');
    form.removeChild(submit);
    inputs.splice(inputs.indexOf(submit), 1);

    let status_display = document.createElement('span');
    status_display.classList.add('status-display', 'hidden');
    settings_section.insertBefore(status_display, settings_section.childNodes[0]);

    // silently send_settings in case the user changed settings while the page was loading
    send_settings(get_all_inputs());

    let viewer_update_interval = 1500;

    function fetch_viewer(){
        viewer_update_interval *= 2;
        viewer_update_interval = Math.min(30000, viewer_update_interval);
        return fetch('/api/viewer', {
            credentials: 'same-origin',
        })
            .then(resp => {
                if(!resp.ok){
                    if(resp.status == 403){
                        // user was logged out in another client
                        window.location = '/';
                    }
                    return Promise.reject(resp);
                }
                return resp; })
            .then(resp => resp.json());
    }

    let last_viewer = {};
    function update_viewer(viewer){
        let dumped = JSON.stringify(viewer);
        if(last_viewer == dumped){
            return;
        }
        last_viewer = dumped;

        document.querySelector('#post-count').textContent = viewer.post_count;
        document.querySelector('#eligible-estimate').textContent = viewer.eligible_for_delete_estimate;
        document.querySelector('#display-name').textContent = viewer.display_name || viewer.screen_name;
        document.querySelector('#display-name').title = '@' + viewer.screen_name;
        document.querySelector('#avatar').src = viewer.avatar_url;
        viewer_update_interval = 1500;

        if(viewer.next_delete){
            viewer.next_delete = new Date(viewer.next_delete);
        }
        if(viewer.last_delete){
            viewer.last_delete = new Date(viewer.last_delete);
        }
        banner.set(viewer);
    }

    let viewer_from_dom = JSON.parse(document.querySelector('script[data-viewer]').textContent)

    update_viewer(viewer_from_dom)

    function set_viewer_timeout(){
        setTimeout(() => fetch_viewer().then(update_viewer).then(set_viewer_timeout, set_viewer_timeout),
            viewer_update_interval);
    }
    set_viewer_timeout();

    banner.on('toggle', enabled => {
        send_settings({policy_enabled: enabled}).then(fetch_viewer).then(update_viewer);
        // TODO show error or spinner if it takes over a second
    })

    let reason_banner = document.querySelector('.banner[data-reason]');
    if(reason_banner){
        let dismiss = reason_banner.querySelector('input[type=submit]');
        dismiss.addEventListener('click', e => {
            e.preventDefault();

            // we don't care if this succeeds or fails. worst
            // case scenario the banner appears again on a future page load
            fetch('/api/reason', {method: 'DELETE', credentials:'same-origin'});

            reason_banner.parentElement.removeChild(reason_banner);
        })
    }

    let archive_form_el = document.querySelector('#archive-form');
    if(archive_form_el){
        let csrf_token = archive_form_el.querySelector('input[name=csrf-token]').value;
        let archive_form = new ArchiveForm({
            target: archive_form_el,
            hydrate: true,
            data: {
                action: archive_form_el.action,
                csrf_token: csrf_token,
            },
        })
    }

    function bump_instance(instance_name){
        let known_instances = known_load();
        let found = false;
        for(let instance of known_instances){
            if(instance['instance'] == instance_name){
                instance.hits ++;
                found = true;
                break;
            }
        }
        if(!found){
            let instance = {"instance": instance_name, "hits": 1};
            known_instances.push(instance);
        }

        known_save(known_instances);

    }

    if(viewer_from_dom['service'] == 'mastodon' && location.hash == '#bump_instance'){
        bump_instance(viewer_from_dom['id'].split('@')[1])
        let url = new URL(location.href)
        url.hash = '';
        history.replaceState('', '', url);
    }
})();
