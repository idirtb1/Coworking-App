# Coworking App

Ce projet est une application web de réservation de salles de coworking. Elle utilise plusieurs services Azure pour offrir une solution complète, incluant la gestion des salles, la réservation par créneau horaire, l’envoi automatisé d’e-mails de confirmation, ainsi que l’hébergement et le stockage des données.

## Fonctionnalités

- **Liste des salles** : Affichage des différentes salles de coworking, leur capacité, et leur description.
- **Réservation** : Sélection d’une salle, d’un créneau horaire, et d’une date. Vérification de la disponibilité.
- **Envoi d’e-mails de confirmation** : Une fois la réservation effectuée, un e-mail de confirmation est envoyé automatiquement via Azure Logic Apps.
- **Gestion centralisée des données** : Stockage des informations des salles et des réservations dans Azure SQL Database.

## Architecture & Services Azure Utilisés

- **Azure App Service** : Héberge l’application Flask (conteneurisée via Docker).
- **Azure SQL Database** : Stocke les données (tables `rooms` et `reservations`).
- **Azure Storage (optionnel)** : Peut héberger des images, comme les photos des salles.
- **Azure Logic Apps** : Automatisation de l’envoi d’e-mails de confirmation après chaque réservation.

## Prérequis

- Compte Azure actif.
- Python 3.9+ installé localement (pour le développement).
- Docker installé localement (pour construire l’image conteneurisée).
- Accès à Docker Hub (ou un autre registre de conteneurs) pour pousser l’image.

## Installation et Déploiement Local

1. **Cloner le dépôt** :  
   ```bash
   git clone https://github.com/idirtb1/Coworking-App.git
   cd Coworking-App
   ```

2. **Installer les dépendances** :  
   ```bash
   pip install -r requirements.txt
   ```
   
3. **Exécuter l’application en local** :  
   ```bash
   python app.py
   ```
   Accédez à `http://localhost:5000` pour voir l’application en local (sans Docker).

## Conteneurisation et Déploiement sur Azure

1. **Construire l’image Docker** :  
   ```bash
   docker build -t idirb/flask-coworking:latest .
   ```

2. **Pousser l’image sur Docker Hub** :  
   ```bash
   docker push idirb/flask-coworking:latest
   ```

3. **Configurer Azure App Service** :  
   - Créez un App Service (Web App for Containers).
   - Configurez l’URL du conteneur (idirb/flask-coworking:latest).
   - Définissez les variables d’environnement (DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD) dans les Paramètres d’Application.

4. **Configurer Azure SQL Database** :  
   - Créez la base de données et les tables `rooms` et `reservations`.
   - Ajoutez quelques enregistrements de salles pour tester.

5. **Configurer Azure Logic Apps** :  
   - Créez une Logic App avec un déclencheur HTTP.
   - Ajoutez une action "Send email" Outlook.
   - Copiez l’URL fournie par la Logic App et mettez à jour votre code Flask pour appeler cette URL après une réservation.

6. **Redémarrer l’App Service** :  
   Après modification des variables ou changement d’image, redémarrez l’App Service depuis le portail Azure.

## Utilisation

- Accédez à l’URL de l’App Service flask-coworking-app-a6gebgeuc7g2dsgc.francecentral-01.azurewebsites.net .
- Consultez la liste des salles.
- Réservez une salle pour un créneau donné.
- Un e-mail de confirmation sera envoyé (si configuré) via la Logic App.

## Défis et Solutions

- Gestion des variables d’environnement dans App Service (sécurité des identifiants).
- Configuration du firewall sur le serveur SQL pour autoriser les connexions depuis l’App Service.
- Intégration de la Logic App (format JSON des données, champs nécessaires).

## Leçons Apprises

- Déploiement d’une application conteneurisée sur Azure App Service.
- Gestion d’une base de données managée (Azure SQL).
- Intégration d’une Logic App pour l’automatisation des tâches (envoi d’emails).
- Importance des variables d’environnement et de la configuration réseau.

## Contribution

Les contributions sont les bienvenues. Ouvrez une issue ou une pull request pour suggérer des améliorations ou corriger des bugs.
