Proyecto Flask — Banco Ficticio (Seguridad/API 5)

Aplicación web desarrollada en Flask (Python) para simular un sistema bancario con distintos roles (administrador, empleado y cliente).
Este proyecto forma parte de un trabajo práctico de Seguridad de Aplicaciones Web, enfocado en la vulnerabilidad API5: Broken Function Level Authorization del estándar OWASP API Security Top 10. 

Descripción

El sistema reproduce un entorno bancario ficticio donde diferentes tipos de usuarios acceden a secciones específicas de la aplicación:

Administrador: gestión general del sistema.

Empleado: operaciones internas.

Cliente: área de usuario.

El objetivo del proyecto es mostrar los riesgos de una mala implementación de autorización por nivel de función (API5), donde un usuario puede acceder a funciones restringidas sin los permisos correspondientes.

Características

Uso de Blueprints para modularizar la aplicación (auth, administrador, empleado, cliente).

Sistema básico de autenticación y sesiones.

Integración con base de datos inicializada mediante init_db().

Plantillas HTML organizadas en la carpeta app/templates.

Archivos estáticos en app/static (CSS, JS, imágenes).

Objetivo educativo

Este proyecto está diseñado con fines académicos y de aprendizaje.
Su propósito es demostrar vulnerabilidades relacionadas con la autorización por nivel de función (Broken Function Level Authorization).


