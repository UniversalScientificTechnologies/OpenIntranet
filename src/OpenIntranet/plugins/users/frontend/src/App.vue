<template>
    <div id="wrapper">
        <header-bar :current-user="currentUser"/>
        <div id="app">
            <div id="nav">
                <router-link to="/">Home</router-link>
                |
                <router-link to="/attendance">Docházka</router-link>
                |
                <router-link to="/attendance/sudo">Docházka Sudo</router-link>
                |
                <router-link to="/users">Uživatelé</router-link>
                |
                <router-link to="/users/sudo">Uživatelé Sudo</router-link>
            </div>
            <router-view/>
        </div>
    </div>
</template>

<script>
    import HeaderBar from "./components/HeaderBar";
    import Axios from "axios";

    export default {
        components: {HeaderBar},
        data() {
            return {
                currentUser: null
            }
        },
        async created() {
            Axios.get("/users/api/users/current")
                .then(res => console.log(this.currentUser = res.data))
                .catch(err => console.log(err))
        }
    }
</script>

<style>

    #app {
        font-family: Avenir, Helvetica, Arial, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        text-align: center;
        color: #2c3e50;
        overflow: auto;
        position: absolute;
        top: 5em;
        bottom: 0;
        left: 0;
        right: 0;
    }

    #nav {
        padding: 30px;
    }

    #nav a {
        font-weight: bold;
        color: #2c3e50;
    }

    #nav a.router-link-exact-active {
        color: #42b983;
    }
</style>
