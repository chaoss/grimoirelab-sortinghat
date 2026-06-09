import routes from './routes'
import dateFormatter from "../src/plugins/dateFormatter";
import setupApolloProvider from '../src/apollo/provider'
import logger from "../src/plugins/logger";
import errorMessages from "../src/plugins/errors";
import { store } from './store';

export default {
  install: (app, options) => {
    const apolloProvider = setupApolloProvider(options.apiURL, options.router, store)

    app.use(apolloProvider)
    app.use(dateFormatter)
    app.use(logger)
    app.use(errorMessages)
    app.use(store)
  },
  routes
}
