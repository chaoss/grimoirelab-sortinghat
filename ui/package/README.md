# sortinghat-ui-core

Exposes a Vue plugin and routes for the SortingHat UI core views.

## Installation and configuration

Install the package in your project.

```
$ yarn add <package tarball URL>
```

Add the plugin and styles to your Vue app in `main.js`.

```
import sortinghat from "sortinghat-ui-core"
import 'sortinghat-ui-core/dist/sortinghat-ui.css'

app.use(sortinghat, {
  apiURL : <sortinghat API URL>,
  router: <vue router instance>
})
```

## Development

To test your changes locally, build and link the package to use it into your
current project. Use `yarn build --watch` to rebuild when the code changes.

```
cd sortinghat/ui/package
yarn build
yarn link

cd path-to-project
yarn link "sortinghat-ui-core"
```

To reverse this process, use `yarn unlink` and `yarn unlink "sortinghat-ui-core"`.

## Building for release

Use `yarn pack` to create a compressed gzip archive of the package.
