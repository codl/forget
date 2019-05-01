import svelte from 'rollup-plugin-svelte';
import node_resolve from 'rollup-plugin-node-resolve';

export default {
    output: {
        format: 'iife',
    },
    plugins: [
        svelte({
            include: 'components/**/*.html',
            hydratable: true,
        }),
        node_resolve(),
    ]
}
