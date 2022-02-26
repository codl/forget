import {SLOTS, normalize_known, known_load, known_save} from './known_instances.js';

(function instance_buttons(){

    const mastodon_container = document.querySelector('#mastodon_instance_buttons');
    const mastodon_button_template = Function('first', 'instance',
        'return `' + document.querySelector('#mastodon_instance_button_template').innerHTML + '`;');
    const mastodon_another_button_template = Function(
        'return `' +
            document.querySelector('#mastodon_another_instance_button_template').innerHTML + '`;');
    const mastodon_top_instances =
        Function('return JSON.parse(`' + document.querySelector('#mastodon_top_instances').innerHTML + '`);')();

    const misskey_container = document.querySelector('#misskey_instance_buttons');
    const misskey_button_template = Function('first', 'instance',
        'return `' + document.querySelector('#misskey_instance_button_template').innerHTML + '`;');
    const misskey_another_button_template = Function(
        'return `' +
            document.querySelector('#misskey_another_instance_button_template').innerHTML + '`;');
    const misskey_top_instances =
        Function('return JSON.parse(`' + document.querySelector('#misskey_top_instances').innerHTML + '`);')();

    async function get_known(){
        let known = known_load();
        if(!known){
            let resp = await fetch('/api/known_instances');
            if(resp.ok && resp.headers.get('content-type') == 'application/json'){
                known = await resp.json();
            }
            else {
                known = {
                    mastodon:[{
                        "instance": "mastodon.social",
                        "hits": 0
                    }],
                    misskey:[{
                        "instance": "misskey.io",
                        "hits": 0
                    }],
                };
            }
            known_save(known)
            fetch('/api/known_instances', {method: 'DELETE'})
        }

        return known;
    }

    function replace_buttons(top_instances, known_instances, container,
            template, template_another_instance){
        let filtered_top_instances = []
        for(let instance of top_instances){
            let found = false;
            for(let k of known_instances){
                if(k['instance'] == instance['instance']){
                    found = true;
                    break;
                }
            }
            if(!found){
                filtered_top_instances.push(instance)
            }
        }

        let instances = known_instances.concat(filtered_top_instances).slice(0, SLOTS);

        let html = '';

        let first = true;
        for(let instance of instances){
            html += template(first, instance['instance'])
            first = false;
        }

        html += template_another_instance();

        container.innerHTML = html;
    }

    async function init_buttons(){
        let known = await get_known();

        known.mastodon = normalize_known(known.mastodon);
        known.misskey = normalize_known(known.misskey);
        known_save(known);

        replace_buttons(mastodon_top_instances, known.mastodon,
            mastodon_container, mastodon_button_template,
            mastodon_another_button_template);
        replace_buttons(misskey_top_instances, known.misskey,
            misskey_container, misskey_button_template,
            misskey_another_button_template);
    }

    init_buttons();
})();
