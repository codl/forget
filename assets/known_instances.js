const STORAGE_KEY = 'forget_known_instances@2021-12-09';
export const SLOTS = 5;

function load_and_migrate_old(){
    const OLD_KEY = "forget_known_instances";
    let olddata = localStorage.getItem(OLD_KEY);
    if(olddata != null){
        olddata = JSON.parse(olddata)
        let newdata = {
            mastodon: olddata,
            misskey: [{
                "instance": "misskey.io",
                "hits": 0
            }]
        };
        known_save(newdata);
        localStorage.removeItem(OLD_KEY);
        return newdata;
    }
}

export function known_save(known){
    localStorage.setItem(STORAGE_KEY, JSON.stringify(known));
}

export function known_load(){
    const default_ = {
        mastodon:[{ "instance": "mastodon.social", "hits": 0 }],
        misskey:[{ "instance": "misskey.io", "hits": 0 }],
    };
    // this makes mastodon.social and misskey.io show up on respective first
    // buttons by default even if they are not the most popular instance
    // according to the server

    let known = localStorage.getItem(STORAGE_KEY);
    if(known){
        known = JSON.parse(known);
    } else {
        known = load_and_migrate_old();
    }
    return known || default_;
}

export function normalize_known(known){
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
