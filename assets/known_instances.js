const STORAGE_KEY = 'forget_known_instances';
export const SLOTS = 5;

export function known_save(known){
    localStorage.setItem(STORAGE_KEY, JSON.stringify(known));
}

export function known_load(){
    let known = localStorage.getItem(STORAGE_KEY);
    if(known){
        known = JSON.parse(known);
    }
    return known;
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
