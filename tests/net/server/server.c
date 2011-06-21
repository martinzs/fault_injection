
#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#define BUFSIZE 2


int main(int argc, char *argv[])
{  
    sockaddr_in sockName;                   // "Jméno" soketu
    sockaddr_in clientInfo;                 // Informace o pøipojeném klientovi
    int Socket;                             // Soket
    int port;                               // Èíslo portu
    char buf[BUFSIZE];                      // Pøijímací buffer
    int size;                               // Poèet pøijatých a odeslaných bytù
    socklen_t addrlen;                      // Velikost adresy vzdáleného poèítaèe
    int count = 0;                          // Poèet pøipojení

    if (argc != 2)
    {
        fprintf(stderr, "Pouziti:\n\t%s port\n", argv[0]);
        return 1;
    }
    port = atoi(argv[1]);
    // Vytvoøíme soket - viz minulý díl
    if ((Socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1)
    {
        perror("socket: ");
        return 1;
    }
    // Zaplníme strukturu sockaddr_in
    // 1) Rodina protokolù
    sockName.sin_family = AF_INET;
    // 2) Èíslo portu, na kterém èekáme
    sockName.sin_port = htons(port);
    // 3) Nastavení IP adresy lokální sí»ové karty, pøes kterou je mo¾no se
    //    pøipojit. Nastavíme mo¾nost pøipojit se odkudkoliv. 
    sockName.sin_addr.s_addr = INADDR_ANY;
    // pøiøadíme soketu jméno
    if (bind(Socket, (sockaddr *)&sockName, sizeof(sockName)) == -1)
    {
        perror("bind: ");
        return 1;
    }
       
    char c = 'A';
    while (1)
    {
        char temp[2];
    	sprintf(temp,"%c", c);
        
        addrlen = sizeof(clientInfo);
        if ((size = recvfrom(Socket, buf, BUFSIZE - 1, 0, (sockaddr *)&clientInfo, &addrlen)) == -1)
        {
            perror("recvfrom: ");
        }
        else
        {
            buf[size] = '\0';
            fprintf(stdout, "recv %s\n", buf);
            fflush(stdout);
        }

        if (sendto(Socket, temp, strlen(temp), 0, (sockaddr *)&clientInfo, addrlen) == -1)
        {
                perror("sendto: ");
        }
        else
        {
            fprintf(stdout, "send %c\n", c);
            fflush(stdout);
        }
        
        if (c == 'Z')
            c = 'A';
        else
            c++;
    }

   

    close(Socket);    
    return 0;
}
