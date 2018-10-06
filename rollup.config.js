import svelte from 'rollup-plugin-svelte';

export default {
    output: {
        format: 'iife',
    },
    plugins: [
        svelte({
            include: 'components/**/*.html',
            hydratable: true,
        }),
    ]
}
