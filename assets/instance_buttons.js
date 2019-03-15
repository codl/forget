(function instance_buttons(){

    const SLOTS = 5;

    const STORAGE_KEY = 'forget_known_instances';

    const container = document.querySelector('#mastodon_instance_buttons');
    const button_template = Function('first', 'instance',
        'return `' + document.querySelector('#instance_button_template').innerHTML + '`;');
    const another_button_template = Function(
        'return `' +
            document.querySelector('#another_instance_button_template').innerHTML + '`;');
    const top_instances =
        Function('return JSON.parse(`' + document.querySelector('#top_instances').innerHTML + '`);')();

    async function get_known(){
        let known = JSON.parse(localStorage.getItem(STORAGE_KEY));
        let has_been_fetched = false;
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
            save(known)
            fetch('/api/known_instances', {method: 'DELETE'})
        }

        return known;
    }

    function normalize(known){
        /*

        move instances with the most hits to the top SLOTS slots,
        making sure not to reorder anything that is already there

        */
        let head = known.slice(0, SLOTS);
        let tail = known.slice(SLOTS);

        if(tail.length == 0){
            return known;
        }

        for(let i = 0; i < SLOTS; i++){
            let head_min = head.reduce((acc, cur) => acc.hits < cur.hits ? acc : cur);
            let tail_max = tail.reduce((acc, cur) => acc.hits > cur.hits ? acc : cur);
            if(head_min.hits < tail_max.hits){
                // swappy
                let i = head.indexOf(head_min);
                let j = tail.indexOf(tail_max);
                let buf = head[i];
                head[i] = tail[j];
                tail[j] = buf;
            }
        }

        return head.concat(tail)
    }

    function save(known){
        localStorage.setItem(STORAGE_KEY, JSON.stringify(known));
    }

    async function replace_buttons(){
        let known = await get_known();

        known = normalize(known);
        save(known);

        let filtered_top_instances = []
        for(let instance of top_instances){
            let found = false;
            for(let k of known){
                if(k['instance'] == instance){
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
