<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <router-link to="/" v-slot="{ href, navigate }">
        <h1
          :href="href"
          @click="navigate"
          class="headline font-weight-light pointer"
        >
          Sorting Hat
        </h1>
      </router-link>

      <v-spacer></v-spacer>
      <v-menu v-if="user && $route.name !== 'Login'" offset-y>
        <template v-slot:activator="{ on }">
          <v-btn depressed small color="primary" v-on="on">
            <v-icon small left>
              mdi-account-circle
            </v-icon>
            {{ user }}
          </v-btn>
        </template>
        <v-list>
          <v-list-item to="/jobs">
            <v-list-item-title>Jobs</v-list-item-title>
          </v-list-item>
          <v-list-item @click="logOut">
            <v-list-item-title>Log out</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>
    <transition name="fade" mode="out-in">
      <router-view />
    </transition>
  </v-app>
</template>

<script>
import Cookies from "js-cookie";
export default {
  name: "App",
  computed: {
    user() {
      return this.$store.state.user;
    }
  },
  methods: {
    logOut() {
      Cookies.remove("sh_authtoken");
      Cookies.remove("sh_user");
      this.$router.push("/login");
      this.$logger.info(`Log out user ${this.user}`);
    }
  }
};
</script>
<style lang="scss">
@import "styles/index.scss";
.fade-enter-active,
.fade-leave-active {
  transition-duration: 0.3s;
  transition-property: opacity;
  transition-timing-function: ease;
}

.fade-enter,
.fade-leave-active {
  opacity: 0;
}
.pointer {
  cursor: pointer;
}
</style>
