(function instance_buttons(){

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
                known = [];
            }
            localStorage.setItem(STORAGE_KEY, JSON.stringify(known));
            fetch('/api/known_instances', {method: 'DELETE'})
        }

        return known;
    }

    async function replace_buttons(){
        let known = await get_known();

        let instances = known.concat(top_instances).slice(0, 5);

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
