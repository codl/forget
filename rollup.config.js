import svelte from 'rollup-plugin-svelte';
import node_resolve from 'rollup-plugin-node-resolve';

export default {
    output: {
        format: 'iife',
    },
    plugins: [
        svelte({
            extensions: ['.html'],
            include: 'components/**/*.html',
            compilerOptions: {hydratable: true},
            emitCss: false,
        }),
        node_resolve(),
    ]
}
