import {SLOTS, normalize_known, known_load, known_save} from './known_instances.js';

(function instance_buttons(){

    const container = document.querySelector('#mastodon_instance_buttons');
    const button_template = Function('first', 'instance',
        'return `' + document.querySelector('#instance_button_template').innerHTML + '`;');
    const another_button_template = Function(
        'return `' +
            document.querySelector('#another_instance_button_template').innerHTML + '`;');
    const top_instances =
        Function('return JSON.parse(`' + document.querySelector('#top_instances').innerHTML + '`);')();

    async function get_known(){
        let known = known_load();
        if(!known){
            let resp = await fetch('/api/known_instances');
            if(resp.ok && resp.headers.get('content-type') == 'application/json'){
                known = await resp.json();
            }
            else {
                known = [{
                    "instance": "mastodon.social",
                    "hits": 0
                }];
            }
            known_save(known)
            fetch('/api/known_instances', {method: 'DELETE'})
        }

        return known;
    }


    async function replace_buttons(){
        let known = await get_known();

        known = normalize_known(known);
        known_save(known);

        let filtered_top_instances = []
        for(let instance of top_instances){
            let found = false;
            for(let k of known){
                if(k['instance'] == instance['instance']){
                    found = true;
                    break;
                }
            }
            if(!found){
                filtered_top_instances.push(instance)
            }
        }

        let instances = known.concat(filtered_top_instances).slice(0, SLOTS);

        let html = '';

        let first = true;
        for(let instance of instances){
            html += button_template(first, instance['instance'])
            first = false;
        }

        html += another_button_template();

        container.innerHTML = html;
    }

    replace_buttons();
})();
