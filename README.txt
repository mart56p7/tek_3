Aflevering af obligatorisk opgave i teknik

Navn: Martin Kjeldgaard Nikolajsen
Klasse: Dat18a


Der er udviklet en simpel protocol ud fra de krav der er givet fra dig.

Server krav:
Max antal pakker per sekund:
Som standard er det sat til 25, men man kan i server.ini �ndre det til et andet tal.

Connection timeout:
Hvis der ikke har v�ret kommunikation mellem server og klient i 4 sekunder lukkes forbindelsen (serverne modtager ikke pakker, hvis den har modtaget mere end max antal pakker i et sekund).

3 way handshake:
Client sender til Server: com-0 <clientIP>
Server sender til Client: com-0 accept <serverIP>
Client sender til Server: com-0 accept
Clients der ikke har lavet 3 way handshake vil der ikke blive svaret til.

Heartbeat:
Client sender til Server: con-h 0x00
Server s�rger for at forbindelsen f�rst kan lukkes 4 sekunder efter modtaget pakke fra klienten.

Server kan rette forbindelsen:
Hvis serveren modtager en kommando den ikke forst�r, s� 
Server sender til Client: con-res 0xFE
con-res 0xFE betyder at forbindelsen bliver lukket.

Hvis serveren modtager kommandoen con-res 0xFF s� g�r den ikke noget.

Besked nummer:
Serveren modtager fra Client: msg-<msgnum>=<besked>
Serveren svare til Client: res-<msgnum+1>=I am server

Implementering:
P� serveren er der brugt et dictionary til at holde styr p� de forskellige klienter. Der bliver brugt en tr�d til at holde styr p� hvor mange pakker der er kommet i det sidste sekund.



Klient krav:
Heartbeat:
Klient sender hvert 3 sekund en pakke til serveren, hvis der ikke har v�ret anden kommunikation.
Om heart beat er sl�et til eller ej, angives i client.ini

Der er indbygget s� klienten kan tale med serveren ud fra de krav der er opstillet til serveren.
Klienten er lavet som en klasse, s� det er nemt at instantere flere klienter, s� der kan v�re flere der taler med serveren samtidig.